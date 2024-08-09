# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0.

'''
Amazon Kinesis Video Stream (KVS) Consumer Library for Python. 

This library parses streaming bytes (chunks) made available by the StreamingBody returned from calls 
to the KVS Media Client GetMedia and KVS Archive Media Client GetMediaForFragmentList
API. 

The Amazon Kinesis Video Stream (KVS) Consumer Library for Python reads in streaming bytes as they become 
available and parses to individual MKV fragments. The library is threaded and non-blocking, 
once a stream is being read it forwards received MKV fragments to named call-backs in the users application.

Fragments are returned as raw bytes and a searchable DOM like structure by parsing with EMBLite by MideTechnology.

The consumer library provides the following functions to further process parsed MKV fragments:
1) get_fragment_tags(): Extract MKV tags from the fragment.
2) save_fragment_as_local_mkv(): Saves the fragment as stand-alone MKV file on local disk.
3) get_frames_as_ndarray(): Returns a ratio of frames in the fragment as a list of NDArray objects.
4) save_frames_as_jpeg(): Returns a ratio of frames in the fragment as a JPEGs to local disk.

Workflow:
1) Define a on_fragment_arrived and on_read_stream_complete call-backs in user application logic. These to process
fragments as they are received and to handle the parser reaching the end of the stream. (When no more fragments are left),
2) Initialize the KVS Media and / or Archive Media clients,
3) Make a call to KVS Media GetMedia and / or KVS Archive Media GetMediaForFragmentList for the given stream,
4) Initialize this KVS Consumer library and call get_streaming_fragements providing the response from the GetMedia
or GetMediaForFragmentList call,
5) Fragments will then be parsed and delivered to the call-backs for processing as per the example code provided.

Credits:
# EMBLite by MideTechnology is an external EBML parser found at https://github.com/MideTechnology/ebmlite
# For convenance a slightly modified version of EMBLite is shipped with the KvsConsumerLibrary but adding credit where its due. 
# EMBLite MIT License: https://github.com/MideTechnology/ebmlite/blob/development/LICENSE

 '''
 
__version__ = "0.0.1"
__status__ = "Development"
__copyright__ = "Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved."
__author__ = "Dean Colcott <https://www.linkedin.com/in/deancolcott/>"

import timeit
import logging
from threading import Thread
from amazon_kinesis_video_consumer_library.ebmlite import loadSchema

# Init the logger.
log = logging.getLogger(__name__)


class KvsConsumerLibrary(Thread):

    def __init__(self, 
                stream_name, 
                get_media_response_object, 
                on_fragment_arrived, 
                on_read_stream_complete, 
                on_read_stream_exception):
        '''
            Initialize the KVS media consumer library
        '''
        # Call the Thread class's init function
        Thread.__init__(self)

        # Used to trigger graceful exit of this thread
        self._stop_get_media = False

        # Init the local vars. 
        log.info('Initilizing KvsConsumerLibrary...')
        self.stream_name = stream_name
        self.get_media_response_object = get_media_response_object
        self.on_fragment_arrived_callback = on_fragment_arrived
        self.on_read_stream_complete_callback = on_read_stream_complete
        self.on_read_stream_exception = on_read_stream_exception

        log.info('Loading EBMLlite MKV Schema....')
        self.schema = loadSchema('matroska.xml')
    
    def _get_ebml_header_elements(self, fragement_dom):
        '''
        Returns the EBML Header elements in the Fragment DOM. EBML Header elements indicate the start 
        of a new fragment and so we use them to set the byte boundaries of individual fragments as they
        arrive in the raw data stream (chunks).

        ### Parameters:

            **fragment_dom**: ebmlite.core.Document <ebmlite.core.MatroskaDocument>
                The DOM like structure describing the fragment parsed by EBMLite. 

        '''
        ebml_header_elements = []
        # Iterate through the fragment elements and capture any EBML Fragment headers (indicating the start of a new fragment)
        for element in fragement_dom:
                if (element.id == 0x1A45DFA3):   # EBML (Master) element ID = 0x1A45DFA3 (440786851 dec)
                    ebml_header_elements.append(element)
        
        return ebml_header_elements

    def _get_simple_block_elements(self, fragement_dom):
        '''
        Returns the DOM SimpleBlock elements found in the fragment. 
        SimpleBlock Elements store the payload of the MKV fragemeny - typically H.264/265 frames but 
        can be any data playload that was ingested by the KVS producer.

        ### Parameters:

            **fragment_dom**: ebmlite.core.Document <ebmlite.core.MatroskaDocument>
                The DOM like structure describing the fragment parsed by EBMLite. 
        
        '''
        simple_block_elements = []
        # Iterate through the fragment elements and capture any Simple Block type elements. 
        # These carry the fragments payload bytes (typically image frames as raw bytes.)
        for element in fragement_dom:
                if (element.id == 0x18538067):                          # Segment element ID = 0x18538067
                    
                    for segement_child in element:
                        if (segement_child.id == 0x1F43B675):           # Cluster element ID = 0x1F43B675

                            for cluster_child in segement_child:
                                if (cluster_child.id == 0xA3):          # SimpleBlock element ID = xA3
                                    simple_block_elements.append(cluster_child)

        return simple_block_elements

    def stop_thread(self):
        self._stop_get_media = True

    ####################################################
    # Read and parse streaming media from a Kinesis Video Stream
    def run(self):
        '''
        Reads in chunks (unframed number of raw bytes) from a KVS GetMedia or GetMediaForFragmentList Streaming Body response 
        and parses into bounded MKV fragments. Raw data is buffered until a complete fragment is received which is then forwarded to the 
        on_fragmemt_arrived callback. Fragment is delivered as a raw byte array and also a parsed EBMLite Document that is a DOM like 
        structure of the elements (including Tags) within the given Fragment. 

        Kinesis Video will continually update the streaming buffer with media as soon as its available. For StartSelectorType = NOW,
        bytes from the media stream will be available as fast as they arrive into Kinesis Video by the producer. In this case the 
        consumer bandwidth and fragment rate will be equal to that of the producer. However, if StartSelector is set to sometime 
        in the past then all fragments from start to end time will be available immediately. The effect is this will 
        read in bytes as fast as the system resources (KVS limits, CPU and bandwidth) will allow until the stream has 
        caught up with the leading edge of media being generated.

        '''

        try:
            # Get the steam botocore.response.Streamingody object from the provided GetMedia response
            kvs_streaming_buffer=self.get_media_response_object['Payload']

            #########################################
            # Iterate through reading and parsing streaming body response of KVS GET Media API call to MKV fragments.
            #########################################
            chunk_buffer = bytearray()
            fragment_read_start_time = timeit.default_timer()

            chunk_read_count = 0
            
            # Uses the StreamingBody object iterator to read in (default 1024 byte) chunks from the streaming buffer.
            for chunk in kvs_streaming_buffer:

                if self._stop_get_media:
                    break

                # Append chunk bytes to ByteArray buffer while waiting for the entire MKV fragment to arrive.
                chunk_buffer.extend(chunk)

                #############################################
                # Parse current byte buffer to MKV EBML DOM like object using EBMLite
                #############################################
                fragement_intrum_dom = self.schema.loads(chunk_buffer)

                #############################################
                #  Process a complete fragment if its arrived and send to the on_fragment_arrived callback. 
                #############################################
                # EBML header elements indicate the start of a new fragment. Here we check if the start of a second fragment
                # has arrived and use its start to identify the byte boundary of the first complete fragment to process.
                ebml_header_elements = self._get_ebml_header_elements(fragement_intrum_dom)

                # If multiple fragment headers then the first fragment has been received completely and ready to process.
                if (len(ebml_header_elements) > 1):
                    
                    # Get the offset for the first and second fragments. First fragment offset should be zero or fragment boundary is out of sync!
                    first_ebml_header_offset = ebml_header_elements[0].offset 
                    second_ebml_header_offset = ebml_header_elements[1].offset 

                    # Isolate the bytes from the first complete MKV fragments in the received chunk data
                    fragment_bytes = chunk_buffer[first_ebml_header_offset : second_ebml_header_offset]

                    # Parse the complete fragment as EBML to a DOM like object
                    fragment_dom = self.schema.loads(fragment_bytes)

                    # Calculate duration taken receiving this fragment - just for telemetry of the steaming data. 
                    fragment_receive_duration = timeit.default_timer() - fragment_read_start_time
                    
                    # Forward fragment to the on_fragment_arrived callback.
                    self.on_fragment_arrived_callback(self.stream_name, 
                                                      fragment_bytes, 
                                                      fragment_dom, 
                                                      fragment_receive_duration)

                    # Remove the processed MKV segment from the raw byte chunk_buffer
                    chunk_buffer = chunk_buffer[second_ebml_header_offset: ]

                    # Reset the chunk read count. 
                    chunk_read_count = 0

                    # Reset the start time for the next segment iteration just to time fragment durations
                    fragment_read_start_time = timeit.default_timer()
                
                #############################################
                # Increment to chunk read count for this fragment
                chunk_read_count +=1

            #############################################
            # Exit the thread if the stream has no more chunks.
            #############################################
            #call the on_stream_read_complete() callback and exit the thread.
            self.on_read_stream_complete_callback(self.stream_name)

        except Exception as err:
            # Pass any exceptions to exception callback.
            self.on_read_stream_exception(self.stream_name, err)
        

