# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0.

'''
Amazon Kinesis Video Stream (KVS) Consumer Library for Python. 

This class provides post-processing fiunctions for a MKV fragement that has been parsed
by the Amazon Kinesis Video Streams Cosumer Library for Python. 

 '''
 
__version__ = "0.0.1"
__status__ = "Development"
__copyright__ = "Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved."
__author__ = "Dean Colcott <https://www.linkedin.com/in/deancolcott/>"

import io
import logging
import amazon_kinesis_video_consumer_library.ebmlite.util as emblite_utils
import wave
import amazon_kinesis_video_consumer_library.ebmlite.decoding as ebmlite_decoding

# Init the logger.
log = logging.getLogger(__name__)

class KvsFragementProcessor():

    ####################################################
    # Fragment processing functions

    def get_fragment_tags(self, fragment_dom):
        '''
        Parses a MKV Fragment Doc (of type ebmlite.core.MatroskaDocument) that is returned to the provided callback 
        from get_streaming_fragments() in this class and returns a dict of the SimpleTag elements found. 

        ### Parameters:

            **fragment_dom**: ebmlite.core.Document <ebmlite.core.MatroskaDocument>
                The DOM like structure describing the fragment parsed by EBMLite. 

        ### Returns:

            simple_tags: dict

            Dictionary of all SimpleTag elements with format -  TagName<String> : TagValue <String | Binary>. 

        '''

        # Get the Segment Element of the Fragment DOM - error if not found
        segment_element = None
        for element in fragment_dom:
            if (element.id == 0x18538067):          # MKV Segment Element ID
                segment_element = element
                break
        
        if (not segment_element):
            raise KeyError('Segment Element required but not found in fragment_doc' )

        # Save all of the SimpleTag elements in the Segment element
        simple_tag_elements = []
        for element in segment_element:
            if (element.id == 0x1254C367):                      # Tags element type ID
                    for tags in element:
                        if (tags.id == 0x7373):                 # Tag element type ID
                            for tag_type in tags:
                                if (tag_type.id == 0x67C8 ):    # SimpleTag element type ID
                                    simple_tag_elements.append(tag_type)

        # For all SimpleTags types (ID: 0x67C8), save for TagName (ID: 0x7373) and values of TagString (ID:0x4487) or TagBinary (ID: 0x4485 )
        simple_tags_dict = {}
        for simple_tag in simple_tag_elements:

            tag_name = None
            tag_value = None
            for element in simple_tag:
                if (element.id == 0x45A3):                              # Tag Name element type ID
                    tag_name = element.value
                elif (element.id == 0x4487 or element.id == 0x4485):    # TagString and TagBinary element type IDs respectively
                    tag_value = element.value
            
            # As long as tag name was found add the Tag to the return dict. 
            if (tag_name):
                simple_tags_dict[tag_name] = tag_value

        return simple_tags_dict
    
    def get_fragement_dom_pretty_string(self, fragment_dom):
        '''
        Returns the Pretty Print parsing of the EBMLite fragment DOM as a string

        ### Parameters:

            **fragment_dom**: ebmlite.core.Document <ebmlite.core.MatroskaDocument>
                The DOM like structure describing the fragment parsed by EBMLite. 

        ### Return:
            **pretty_print_str**: str
                Pretty print string of the Fragment DOM object
        '''
        
        pretty_print_str = io.StringIO()

        emblite_utils.pprint(fragment_dom, out=pretty_print_str)
        return pretty_print_str.getvalue()

    def save_fragment_as_local_mkv(self, fragment_bytes, file_name_path):
        '''
        Save the provided fragment_bytes as stand-alone MKV file on local disk.
        fragment_bytes as it arrives in is already a well formatted MKV fragment 
        so can just write the bytes straight to disk and it will be a playable MKV file. 

        ### Parameters:

        fragment_bytes: bytearray
            A ByteArray with raw bytes from exactly one fragment.

        file_name_path: Str
            Local file path / name to save the MKV file to. 

        '''

        f = open(file_name_path, "wb")
        f.write(fragment_bytes)      
        f.close()
    

    def get_raw_audio_track_from_simple_block(self, mkv_element):
        '''
        This function gets the raw audio track from a SimpleBlock element
        in a Matroska file from Amazon Connect.

        It will remove SimpleBlock header as per: 
        https://github.com/ietf-wg-cellar/matroska-specification/blob/master/notes.md

        Will works only if track number VINT is one octet length.

        ### Parameters:        
            mkv_element: ebmlite.core.Document <ebmlite.core.MatroskaDocument>
                    The DOM like structure describing the fragment parsed by EBMLite.

        ### Return:
            A bytearray containing the raw audio data of the specified track        
        '''

        if mkv_element.name == "SimpleBlock":
            mkv_element.stream.seek(mkv_element.payloadOffset+4)
            return mkv_element.parse(mkv_element.stream, mkv_element.size-4)
        return None
    
    def get_audio_track_number_from_simple_block(self, mkv_element):
        '''
        This function gets the number of audio track from a SimpleBlock element
        in a Matroska file from Amazon Connect.

        Will works only if track number VINT is one octet length as per:
        https://github.com/ietf-wg-cellar/matroska-specification/blob/master/notes.md

        ### Parameters:        
            mkv_element: ebmlite.core.Document <ebmlite.core.MatroskaDocument>
                    The DOM like structure describing the fragment parsed by EBMLite.

        ### Return:
            number of audio track in SimpleBlock     
        '''

        if mkv_element.name == "SimpleBlock":
            mkv_element.stream.seek(mkv_element.payloadOffset)
            ch = mkv_element.stream.read(1)
            length, _ = ebmlite_decoding.decodeIntLength(ord(ch))
            if length == 1:
                '''
                removing VINT_MARKER as per https://datatracker.ietf.org/doc/rfc8794/ paragraph 4
                '''
                track_nr =  ord(ch) & 127

            return track_nr                    
        return None


    def get_track_bytearray(self, mkv_dom, track_nr):
        '''
        This function extracts the raw audio track from a Matroska
        file from Amazon Connect and returns it as a bytearray. It iterates through
        the SimpleBlock elements within each Cluster, alternating which
        track it appends based on the track number.

        ### Parameters:        
            mkv_dom: ebmlite.core.Document <ebmlite.core.MatroskaDocument>
                    The DOM like structure describing the fragment parsed by EBMLite.

            track_nr: The track number (1 or 2) to extract

        ### Return:
            A bytearray containing the raw audio data of the specified track

        '''

        track_bytearray = bytearray()

        for element in mkv_dom:
            for segment_child in element:
                if segment_child.name == "Cluster":
                    i=0
                    for cluster_child in segment_child:
                        if cluster_child.name == "SimpleBlock":
                            simple_block_track_nr =self.get_audio_track_number_from_simple_block(cluster_child)
                            i+=1
                            if track_nr == simple_block_track_nr:
                                track_bytearray.extend(self.get_raw_audio_track_from_simple_block(cluster_child))

        return track_bytearray

    def get_track_number_by_name(self, fragment_dom, track_name):
        '''
        This function gets the track number from a Amazon Connect Matroska fragment  
        by track name.
        
        ### Parameters:
            fragment_dom: ebmlite.core.Document <ebmlite.core.MatroskaDocument>
                The DOM like structure describing the fragment parsed by EBMLite. 

            track_name (str): The name of the track to lookup.
            
        ### Returns:
            int: The track number (as an integer), or None if not found.
        '''
        for element in fragment_dom:

            for segment_child in element:

                if segment_child.name == "Tracks":
                    for cluster_child in segment_child:
                        fragment_dom_track_name = ''
                        fragment_dom_track_number = 0
                        if cluster_child.name == "TrackEntry":
                            for te_child in cluster_child:
                                if te_child.name == "Name":
                                    fragment_dom_track_name = te_child.value
                                if te_child.name == "TrackNumber":
                                    fragment_dom_track_number = te_child.value
                        if fragment_dom_track_name == track_name:
                            return fragment_dom_track_number
        return None
        
        
    def get_connect_fragment_audio_track_from_customer_as_bytes(self, fragment_dom):
        '''
        Gets audio track from the customer in a Amazon Connect Matroska fragment
        as a byte array.
        
        ### Parameters:
            
            fragment_dom: ebmlite.core.Document <ebmlite.core.MatroskaDocument>
                The DOM like structure describing the fragment parsed by EBMLite.

        '''

        track_number =  self.get_track_number_by_name(fragment_dom, "AUDIO_FROM_CUSTOMER")
        if track_number:
            return self.get_track_bytearray(fragment_dom, track_number)
            
            
    def get_connect_fragment_audio_track_tom_customer_as_bytes(self, fragment_dom):
        '''
        Gets audio track to the customer in a Amazon Connect Matroska fragment
        as a byte array.
        
        ### Parameters:
            
            fragment_dom: ebmlite.core.Document <ebmlite.core.MatroskaDocument>
                The DOM like structure describing the fragment parsed by EBMLite.

        '''

        track_number =  self.get_track_number_by_name(fragment_dom, "AUDIO_T_CUSTOMER")
        if track_number:
            return self.get_track_bytearray(fragment_dom, track_number)
     

    def convert_track_to_wav(self, track_bytearray):
        '''
        This function converts a track bytearray to a wav file.
        '''

        file_wav = io.BytesIO()
        with wave.open(file_wav, 'wb') as f:
            f.setnchannels(1)
            f.setframerate(8000)
            f.setsampwidth(2)
            f.writeframes(track_bytearray)
        return file_wav
    
    # def save_connect_fragment_audio_track_as_wav(self, fragment_dom, track_nr, file_name_path):
    #     '''
    #     Save the provided fragment_dom as wav file on local disk.

    #     ### Parameters:

    #         fragment_dom: ebmlite.core.Document <ebmlite.core.MatroskaDocument>
    #             The DOM like structure describing the fragment parsed by EBMLite.

    #         tranck_nr: int
    #             The track number (1 or 2) to extract

    #     file_name_path: Str
    #         Local file path / name to save the MKV file to.

    #     '''

    #     fragment_bytes = self.get_track_bytearray(fragment_dom, track_nr)
    #     fragment_wav = self.convert_track_to_wav(fragment_bytes)
    #     with open(file_name_path, 'wb') as f:
    #         f.write(fragment_wav.getvalue())
    
    # def save_connect_fragment_audio_track_from_customer_as_wav(self, fragment_dom, file_name_path_part):
    #     '''
    #     Saves the audio track from the customer in a Amazon Connect Matroska fragment
    #     as a WAV file.
        
    #     ### Parameters:
            
    #         fragment_dom: ebmlite.core.Document <ebmlite.core.MatroskaDocument>
    #             The DOM like structure describing the fragment parsed by EBMLite.

    #         file_name_path_part (str): The file path to save the WAV file to

    #     '''

    #     track_number =  self.get_track_number_by_name(fragment_dom, "AUDIO_FROM_CUSTOMER")
    #     if track_number:
    #         file_name_path = file_name_path_part + "-AUDIO_FROM_CUSTOMER.wav"
    #         self.save_connect_fragment_audio_track_as_wav(fragment_dom, track_number, file_name_path)

    # def save_connect_fragment_audio_track_to_customer_as_wav(self, fragment_dom, file_name_path_part):
    #     '''
    #     Saves the audio track to the customer in a Amazon Connect Matroska fragment 
    #     as a WAV file.
        
    #     ### Parameters:
            
    #         fragment_dom: ebmlite.core.Document <ebmlite.core.MatroskaDocument>
    #             The DOM like structure describing the fragment parsed by EBMLite.

    #         file_name_path_part (str): The file path to save the WAV file to

    #     '''
    #     track_number =  self.get_track_number_by_name(fragment_dom, "AUDIO_TO_CUSTOMER")
    #     if track_number:
    #         file_name_path = file_name_path_part + "-AUDIO_TO_CUSTOMER.wav"
    #         self.save_connect_fragment_audio_track_as_wav(fragment_dom, track_number, file_name_path)