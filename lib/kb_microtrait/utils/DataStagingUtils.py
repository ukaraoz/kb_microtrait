import os
import time
import glob
import re
import subprocess

from installed_clients.WorkspaceClient import Workspace
from installed_clients.AssemblyUtilClient import AssemblyUtil
from installed_clients.SetAPIServiceClient import SetAPI
from installed_clients.MetagenomeUtilsClient import MetagenomeUtils

class DataStagingUtils(object):

    def __init__(self, config, ctx):
        self.ctx = ctx
        self.scratch = os.path.abspath(config['scratch'])
        self.ws_url = config['workspace-url']
        self.serviceWizardURL = config['srv-wiz-url']
        self.callbackURL = config['SDK_CALLBACK_URL']
        if not os.path.exists(self.scratch):
            os.makedirs(self.scratch)

    def stage_input(self, input_ref, fasta_file_extension):
        '''
        Stage input based on an input data reference for CheckM

        input_ref can be a reference to an Assembly, BinnedContigs, or (not yet implemented) a Genome

        This method creates a directory in the scratch area with the set of Fasta files, names
        will have the fasta_file_extension parameter tacked on.

            ex:

            staged_input = stage_input('124/15/1', 'fna')

            staged_input
            {"input_dir": '...'}
        '''
        # config
        #SERVICE_VER = 'dev'
        SERVICE_VER = 'release'
        [OBJID_I, NAME_I, TYPE_I, SAVE_DATE_I, VERSION_I, SAVED_BY_I, WSID_I, WORKSPACE_I, CHSUM_I, SIZE_I, META_I] = range(11)  # object_info tuple
        ws = Workspace(self.ws_url)

        # 1) generate a folder in scratch to hold the input
        suffix = str(int(time.time() * 1000))
        input_dir = os.path.join(self.scratch, 'genomes_' + suffix)
        if not os.path.exists(input_dir):
            os.makedirs(input_dir)
        fasta_files_filepath = os.path.join(self.scratch, 'genomes_' + suffix + '.fasta_files.txt')

        # 2) based on type, download the files
        obj_name = self.get_data_obj_name (input_ref)
        print('*************' + obj_name + '*************\n\n')
        type_name = self.get_data_obj_type (input_ref)

        # auClient
        try:
            auClient = AssemblyUtil(self.callbackURL, token=self.ctx['token'], service_ver=SERVICE_VER)
        except Exception as e:
            raise ValueError('Unable to instantiate auClient with callbackURL: '+ self.callbackURL +' ERROR: ' + str(e))

        # setAPI_Client
        try:
            #setAPI_Client = SetAPI (url=self.callbackURL, token=self.ctx['token'])  # for SDK local.  local doesn't work for SetAPI
            setAPI_Client = SetAPI (url=self.serviceWizardURL, token=self.ctx['token'])  # for dynamic service
        except Exception as e:
            raise ValueError('Unable to instantiate setAPI_Client with serviceWizardURL: '+ self.serviceWizardURL +' ERROR: ' + str(e))

        # mguClient
        try:
            mguClient = MetagenomeUtils(self.callbackURL, token=self.ctx['token'], service_ver=SERVICE_VER)
        except Exception as e:
            raise ValueError('Unable to instantiate mguClient with callbackURL: '+ self.callbackURL +' ERROR: ' + str(e))


        # Standard Single Assembly
        #
        if type_name in ['KBaseGenomeAnnotations.Assembly']:
            # create file data
            filename = os.path.join(input_dir, obj_name + '.' + fasta_file_extension)
            auClient.get_assembly_as_fasta({'ref': input_ref, 'filename': filename})
            if not os.path.isfile(filename):
                raise ValueError('Error generating fasta file from an Assembly or ContigSet with AssemblyUtil')
            # make sure fasta file isn't empty
            min_fasta_len = 1
            if not self.fasta_seq_len_at_least(filename, min_fasta_len):
                raise ValueError('Assembly or ContigSet is empty in filename: '+str(filename))
            print('\n\n\n' + "FILENAME:" + fasta_files_filepath + '\n')
            # with open(os.path.abspath(file_path), 'rb') as data_file
            with open(fasta_files_filepath, 'w') as fasta_files_filepath_handle:
                fasta_files_filepath_handle.write(filename)

        # AssemblySet
        #
        elif type_name == 'KBaseSets.AssemblySet':
            filenames = []
            # read assemblySet
            try:
                assemblySet_obj = setAPI_Client.get_assembly_set_v1 ({'ref':input_ref, 'include_item_info':1})
            except Exception as e:
                raise ValueError('Unable to get object from workspace: (' + input_ref +')' + str(e))
            assembly_refs = []
            assembly_names = []
            for assembly_item in assemblySet_obj['data']['items']:
                this_assembly_ref = assembly_item['ref']
                # assembly obj info
                try:
                    this_assembly_info = ws.get_object_info_new ({'objects':[{'ref':this_assembly_ref}]})[0]
                    this_assembly_name = this_assembly_info[NAME_I]
                except Exception as e:
                    raise ValueError('Unable to get object from workspace: (' + this_assembly_ref +'): ' + str(e))
                assembly_refs.append(this_assembly_ref)
                assembly_names.append(this_assembly_name)

            # create file data (name for file is what's reported in results)
            for ass_i,assembly_ref in enumerate(assembly_refs):
                this_name = assembly_names[ass_i]
                filename = os.path.join(input_dir, this_name + '.' + fasta_file_extension)
                auClient.get_assembly_as_fasta({'ref': assembly_ref, 'filename': filename})
                if not os.path.isfile(filename):
                    raise ValueError('Error generating fasta file from an Assembly or ContigSet with AssemblyUtil')
                # make sure fasta file isn't empty
                min_fasta_len = 1
                if not self.fasta_seq_len_at_least(filename, min_fasta_len):
                    raise ValueError('Assembly or ContigSet is empty in filename: '+str(filename))
                filenames.append(filename)

            with open(fasta_files_filepath, 'w') as fasta_files_filepath_handle:
                for file in filenames:
                    fasta_files_filepath_handle.write("%s\n" % file)

        # Genome and GenomeSet
        #
        elif type_name == 'KBaseGenomes.Genome' or type_name == 'KBaseSearch.GenomeSet':
            genome_obj_names = []
            genome_sci_names = []
            genome_assembly_refs = []
            filenames = []
                
            if type_name == 'KBaseGenomes.Genome':
                genomeSet_refs = [input_ref]
            else:  # get genomeSet_refs from GenomeSet object
                genomeSet_refs = []
                try:
                    genomeSet_object = ws.get_objects2({'objects':[{'ref':input_ref}]})['data'][0]['data']
                except Exception as e:
                    raise ValueError('Unable to fetch '+str(input_ref)+' object from workspace: ' + str(e))
                    #to get the full stack trace: traceback.format_exc()
            # iterate through genomeSet members
            for genome_id in genomeSet_object['elements'].keys():
                if 'ref' not in genomeSet_object['elements'][genome_id] or \
                    genomeSet_object['elements'][genome_id]['ref'] == None or \
                    genomeSet_object['elements'][genome_id]['ref'] == '':
                        raise ValueError('genome_ref not found for genome_id: '+str(genome_id)+' in genomeSet: '+str(input_ref))
                else:
                    genomeSet_refs.append(genomeSet_object['elements'][genome_id]['ref'])

            # genome obj data
            for i,this_input_ref in enumerate(genomeSet_refs):
                try:
                    objects = ws.get_objects2({'objects':[{'ref':this_input_ref}]})['data']
                    genome_obj = objects[0]['data']
                    genome_obj_info = objects[0]['info']
                    genome_obj_names.append(genome_obj_info[NAME_I])
                    genome_sci_names.append(genome_obj['scientific_name'])
                except:
                    raise ValueError ("unable to fetch genome: "+this_input_ref)

                # Get genome_assembly_ref
                # which sequence is filled for the genome object
                if ('contigset_ref' not in genome_obj or genome_obj['contigset_ref'] == None) \
                  and ('assembly_ref' not in genome_obj or genome_obj['assembly_ref'] == None):
                    msg = "Genome "+genome_obj_names[i]+" (ref:"+input_ref+") "+genome_sci_names[i]+" MISSING BOTH contigset_ref AND assembly_ref.  Cannot process.  Exiting."
                    raise ValueError (msg)
                    continue
                elif 'assembly_ref' in genome_obj and genome_obj['assembly_ref'] != None:
                    msg = "Genome "+genome_obj_names[i]+" (ref:"+input_ref+") "+genome_sci_names[i]+" USING assembly_ref: "+str(genome_obj['assembly_ref'])
                    print (msg)
                    genome_assembly_refs.append(genome_obj['assembly_ref'])
                elif 'contigset_ref' in genome_obj and genome_obj['contigset_ref'] != None:
                    msg = "Genome "+genome_obj_names[i]+" (ref:"+input_ref+") "+genome_sci_names[i]+" USING contigset_ref: "+str(genome_obj['contigset_ref'])
                    print (msg)
                    genome_assembly_refs.append(genome_obj['contigset_ref'])

            # create file data (name for file is what's reported in results)
            for ass_i,assembly_ref in enumerate(genome_assembly_refs):
                this_name = genome_obj_names[ass_i]
                filename = os.path.join(input_dir, this_name + '.' + fasta_file_extension)
                auClient.get_assembly_as_fasta({'ref': assembly_ref, 'filename': filename})
                if not os.path.isfile(filename):
                    raise ValueError('Error generating fasta file from an Assembly or ContigSet with AssemblyUtil')
                # make sure fasta file isn't empty
                min_fasta_len = 1
                if not self.fasta_seq_len_at_least(filename, min_fasta_len):
                    raise ValueError('Assembly or ContigSet is empty in filename: '+str(filename))
                filenames.append(filename)
            
            with open(fasta_files_filepath, 'w') as fasta_files_filepath_handle:
                for file in filenames:
                    fasta_files_filepath_handle.write("%s\n" % file)

        # Unknown type slipped through
        #
        else:
            raise ValueError('Cannot stage fasta file input directory from type: ' + type_name)

        return {'input_dir': input_dir, 'folder_suffix': suffix, 'fasta_files_filepath': fasta_files_filepath}

    def get_data_obj_name(self, input_ref):
        [OBJID_I, NAME_I, TYPE_I, SAVE_DATE_I, VERSION_I, SAVED_BY_I, WSID_I, WORKSPACE_I, CHSUM_I, SIZE_I, META_I] = range(11)  # object_info tuple
        ws = Workspace(self.ws_url)
        input_info = ws.get_object_info3({'objects': [{'ref': input_ref}]})['infos'][0]
        obj_name = input_info[NAME_I]
        #type_name = input_info[TYPE_I].split('-')[0]
        return obj_name

    def get_data_obj_type(self, input_ref, remove_module=False):
        [OBJID_I, NAME_I, TYPE_I, SAVE_DATE_I, VERSION_I, SAVED_BY_I, WSID_I, WORKSPACE_I, CHSUM_I, SIZE_I, META_I] = range(11)  # object_info tuple
        ws = Workspace(self.ws_url)
        input_info = ws.get_object_info3({'objects': [{'ref': input_ref}]})['infos'][0]
        #obj_name = input_info[NAME_I]
        type_name = input_info[TYPE_I].split('-')[0]
        if remove_module:
            type_name = type_name.split('.')[1]
        return type_name

    def fasta_seq_len_at_least(self, fasta_path, min_fasta_len=1):
        '''
        counts the number of non-header, non-whitespace characters in a FASTA file
        '''
        seq_len = 0
        with open (fasta_path, 'r') as fasta_handle:
            for line in fasta_handle:
                line = line.strip()
                if line.startswith('>'):
                    continue
                line = line.replace(' ','')
                seq_len += len(line)
                if seq_len >= min_fasta_len:
                    return True
        return False


