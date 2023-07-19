# -*- coding: utf-8 -*-
import unittest
import os  # noqa: F401
import json  # noqa: F401
import time
import shutil

from os import environ
from configparser import ConfigParser

from pprint import pprint  # noqa: F401

from data import *

from installed_clients.AssemblyUtilClient import AssemblyUtil
from installed_clients.GenomeFileUtilClient import GenomeFileUtil
from installed_clients.MetagenomeUtilsClient import MetagenomeUtils
from installed_clients.SetAPIServiceClient import SetAPI
from installed_clients.WorkspaceClient import Workspace
from installed_clients.KBaseReportClient import KBaseReport

from kb_microtrait.kb_microtraitImpl import kb_microtrait
from kb_microtrait.kb_microtraitServer import MethodContext
from kb_microtrait.authclient import KBaseAuth as _KBaseAuth

from kb_microtrait.utils.microtraitUtil import microtraitUtil
from kb_microtrait.utils.DataStagingUtils import DataStagingUtils


class kb_microtraitTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        token = environ.get('KB_AUTH_TOKEN', None)
        config_file = os.environ.get('KB_DEPLOYMENT_CONFIG', None)
        test_time_stamp = int(time.time() * 1000)

        cls.cfg = {}
        config = ConfigParser()
        config.read(config_file)
        for nameval in config.items('kb_microtrait'):
            cls.cfg[nameval[0]] = nameval[1]
            #print(nameval[0] + '----' + nameval[1] + '\n')
            #print(os.environ['SDK_CALLBACK_URL'] + '\n')
        # Getting username from Auth profile for token
        authServiceUrl = cls.cfg['auth-service-url']
        auth_client = _KBaseAuth(authServiceUrl)
        user_id = auth_client.get_user(token)
        # WARNING: don't call any logging methods on the context object,
        # it'll result in a NoneType error
        cls.ctx = MethodContext(None)
        cls.ctx.update({
            'token': token,
            'user_id': user_id,
            'provenance': [{
                'service': 'kb_microtrait',
                'method': 'please_never_use_it_in_production',
                'method_params': []
            }],
            'authenticated': 1
            })
        cls.wsURL = cls.cfg['workspace-url']
        cls.wsClient = Workspace(cls.wsURL)
        cls.serviceImpl = kb_microtrait(cls.cfg)
        cls.callback_url = os.environ['SDK_CALLBACK_URL']

        cls.scratch = cls.cfg['scratch']
        cls.appdir = cls.cfg['appdir']

        cls.test_data_dir = os.path.join(cls.scratch, 'test_data')
        cls.suffix = test_time_stamp
        #cls.microtrait_runner = microtraitUtil(cls.cfg, cls.ctx)

        cls.wsName = "test_kb_microtrait_" + str(cls.suffix)
        cls.ws_info = cls.wsClient.create_workspace({'workspace': cls.wsName})

        cls.au = AssemblyUtil(os.environ['SDK_CALLBACK_URL'])
        cls.gfu = GenomeFileUtil(os.environ['SDK_CALLBACK_URL'], service_ver='dev')
        cls.mu = MetagenomeUtils(os.environ['SDK_CALLBACK_URL'])
        cls.setAPI = SetAPI(url=cls.cfg['srv-wiz-url'], token=cls.ctx['token'])
        cls.kr = KBaseReport(os.environ['SDK_CALLBACK_URL'])
        #ret = cls.wsClient.create_workspace({'workspace': cls.wsName})  # noqa
        cls.data_loaded = False

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, 'wsName'):
            cls.wsClient.delete_workspace({'workspace': cls.wsName})
            print('Test workspace was deleted')

    def getWsClient(self):
        return self.__class__.wsClient

    def getImpl(self):
        return self.__class__.serviceImpl

    def getContext(self):
        return self.__class__.ctx

    def getConfig(self):
        return self.__class__.serviceImpl.config

    # this is for when testing is done from local files
    # skip if testing directly from kbase references
    #def setUp(self):
    #    print("Running prepare data from setUp")
    #    if not os.path.exists("/kb/module/work/tmp/test_data/assemblies"):
    #        os.makedirs("/kb/module/work/tmp/test_data/assemblies")
    #    self.prepare_data()
    #    print("Done")

    def _prep_assembly(self, assembly):
        '''
        input: dict of assembly data in the form
        {
            'path': '/path/to/assembly/file.fna',
            'name': 'Cool_Assembly_Name',
            'attr': 'assembly_blah_ref', # name of the attribute to populate
        }

        '''
        if hasattr(self, assembly['attr']):
            return

        assembly_file_path = os.path.join(self.test_data_dir, "assemblies", assembly['path'])
        #print("assembly_file_path:", assembly_file_path, "\n\n")
        #dir_path = "/kb/module/work/tmp"
        ##dir_path = os.path.join(self.appdir, "test", "data", "assemblies")
        #print("dir_path:", dir_path, "\n\n")
        #content = os.scandir(dir_path)
        #for item in content:
        #    if item.is_file():
        #        print('FILE: ' + item.path + '\n')
        #    else:
        #        print('DIR: ' + item.path + '\n')
            
        if not os.path.exists(assembly_file_path):
            shutil.copy(os.path.join(self.appdir, "test", "data", "assemblies", assembly['path']), assembly_file_path)

        saved_assembly = self.au.save_assembly_from_fasta({
            'file': {'path': assembly_file_path},
            'workspace_name': self.ws_info[1],
            'assembly_name': assembly['name'],
        })
        setattr(self, assembly['attr'], saved_assembly)
        print({
            'Saved Assembly': saved_assembly,
            assembly['attr']: getattr(self, assembly['attr']),
        })

    def _prep_assemblyset(self, assemblyset):
        '''
        input: dict of assemblyset data in the form:
        {
            'name': 'Cool_AssemblySet_Name',
            'items': [{}]
            'attr': 'assemblyset_blah_ref',
        }

        '''
        if hasattr(self, assemblyset['attr']):
            return
        saved_assembly_set = self.setAPI.save_assembly_set_v1({
            'workspace_name': self.ws_info[1],
            'output_object_name': assemblyset['name'],
            'data': {
                'description': 'test assembly set',
                'items': assemblyset['items'],
            },
        })
        setattr(self, assemblyset['attr'], saved_assembly_set['set_ref'])
        print({
            'Saved AssemblySet': saved_assembly_set,
            assemblyset['attr']: getattr(self, assemblyset['attr']),
        })
        TEST_DATA['assemblyset_list'].append(assemblyset)

    def prep_assemblies(self):
        ''' prepare the assemblies and assembly set '''

        assembly_list = TEST_DATA['assembly_list']

        # just load the test assembly and the dodgy contig assembly
        for assembly in assembly_list:
            self._prep_assembly(assembly)

        assemblyset_list = [
            {   # assembly set composed of the two assemblies above
                'name': 'Test_Assembly_Set',
                'attr': 'assembly_set_ref',
                'items': [
                    {
                        'ref':   getattr(self, a['attr']),
                        'label': a['name'],
                    }
                    for a in assembly_list[0:1]
                ],
            },
        ]

        for assemblyset in assemblyset_list:
            self._prep_assemblyset(assemblyset)

        return True

    def _prep_genome(self, genome):

        if hasattr(self, genome['attr']):
            return

        genome_file_path = os.path.join(self.test_data_dir, genome['path'])
        if not os.path.exists(genome_file_path):
            shutil.copy(os.path.join(self.appdir, "test", "data", "genomes", genome['path']), genome_file_path)

        genome_data = self.gfu.genbank_to_genome({
            'file': {'path': genome_file_path},
            'workspace_name': self.ws_info[1],
            'genome_name': genome['name'],
            'generate_ids_if_needed': 1,
        })
        setattr(self, genome['attr'], genome_data['genome_ref'])
        print({
            'Saved Genome': genome_data,
            genome['attr']: getattr(self, genome['attr']),
        })

    def _prep_genomeset(self, genomeset):

        if hasattr(self, genomeset['attr']):
            return

        [OBJID_I, NAME_I, TYPE_I, SAVE_DATE_I, VERSION_I, SAVED_BY_I, WSID_I,
         WORKSPACE_I, CHSUM_I, SIZE_I, META_I] = list(range(11))  # object_info tuple

        obj_info = self.wsClient.save_objects({
            'workspace': self.ws_info[1],
            'objects': [{
                'type': 'KBaseSearch.GenomeSet',
                'data': {
                    'description': 'genomeSet for testing',
                    'elements': genomeset['items'],
                },
                'name': genomeset['name'],
                'meta': {},
                'provenance': [{
                    'service': 'kb_microtrait',
                    'method':  'test_microtrait'
                }]
            }]
        })[0]
        reference = "/".join([str(obj_info[prop]) for prop in [WSID_I, OBJID_I, VERSION_I]])

        setattr(self, genomeset['attr'], reference)
        print({
            'Saved Genomeset': obj_info,
            genomeset['attr']: getattr(self, genomeset['attr'])
        })

        TEST_DATA['genomeset_list'].append(genomeset)

    def prep_genomes(self):

        ''' add a couple of genomes and create a genome set '''

        genome_list = TEST_DATA['genome_list'][0:3]

        # upload a few genomes
        for genome in genome_list:
            self._prep_genome(genome)

        genomeset_list = [
            {
                # create a genomeSet from the genome_list
                'name': 'Small_GenomeSet',
                'attr': 'genome_set_small_ref',
                'items': {
                    genome['name']: {
                        'ref': getattr(self, genome['attr'])
                    } for genome in genome_list
                },
            },
        ]

        for genomeset in genomeset_list:
            self._prep_genomeset(genomeset)

        return True


    def prepare_data(self):
        print("self.data_loaded:", self.data_loaded, "\n")
        if not self.data_loaded:
            #self.assertTrue(self.prep_assemblies())
            #self.assertTrue(self.prep_genomes())
            #self.assertTrue(self.prep_binned_contigs())
            self.data_loaded = True
        return True

    @unittest.skip
    def test_00_prep_data(self):
        print("In test_00, self.data_loaded:", self.data_loaded, "\n")
        # prepare the test data
        self.assertTrue(self.prepare_data())

    # Test 1: single assembly
    #
    # Uncomment to skip this test
    @unittest.skip("skipped test_run_microtrait_app_single_assembly")
    def test_run_microtrait_app_single_assembly(self):
        method_name = 'test_run_microtrait_app_single_assembly'
        print ("\n=================================================================")
        print ("RUNNING "+method_name+"()")
        print ("=================================================================\n")

        # run microtrait app on a single assembly
        assembly = TEST_DATA['assembly_list'][1]

        input_ref = getattr(self, assembly['attr'])

        #print("^^^^^^^^^^^^^assembly:" + assembly + '\n')
        print("^^^^^^^^^^^^^input_ref:" + input_ref + '\n')
        params = {
            'dir_name': assembly['attr'],
            'workspace_name': self.ws_info[1],
            'input_ref': input_ref,
            'threads': 4
        }
        #expected_results = {
        #    'direct_html_link_index': 0,
        #    'file_links': ['CheckM_summary_table.tsv.zip', 'plots.zip', 'full_output.zip'],
        #    'html_links': [
        #        'CheckM_Plot.html'
        #    ],
        #}
        result = self.getImpl().run_microtrait(self.getContext(), params)[0]

        #self.run_and_check_report(params, expected_results)

    # Test 2: Assembly Set
    #
    # Uncomment to skip this test
    @unittest.skip("skipped test_run_microtrait_app_single_assemblySet")
    def test_run_microtrait_app_single_assemblySet(self):
        method_name = 'test_run_microtrait_app_single_assemblySet'
        print ("\n=================================================================")
        print ("RUNNING "+method_name+"()")
        print ("=================================================================\n")

        # run checkM lineage_wf app on an assembly set
        # input_ref = self.assemblySet_ref1
        assemblyset = TEST_DATA['assemblyset_list'][0]

        input_ref = getattr(self, assemblyset['attr'])
        params = {
            'dir_name': assembly['attr'],
            'workspace_name': self.ws_info[1],
            'input_ref': input_ref,
            'threads': 4
        }
        #expected_results = {
        #    'direct_html_link_index': 0,
        #    'file_links': ['CheckM_summary_table.tsv.zip', 'plots.zip', 'full_output.zip'],
        #    'html_links': [
        #        'CheckM_Plot.html'
        #    ],
        #}
        result = self.getImpl().run_microtrait(self.getContext(), params)[0]

    # Test 3: Single Genome
    #
    # Uncomment to skip this test
    @unittest.skip("skipped test_run_microtrait_app_single_genome")
    def test_run_microtrait_app_single_genome(self):
        method_name = 'test_run_microtrait_app_single_genome'
        print ("\n=================================================================")
        print ("RUNNING "+method_name+"()")
        print ("=================================================================\n")

        # run checkM lineage_wf app on a single genome
        # input_ref = self.genome_refs[0]
        genome = TEST_DATA['genome_list'][1]

        input_ref = getattr(self, genome['attr'])
        params = {
            'dir_name': genome['attr'],
            'workspace_name': self.ws_info[1],
            'input_ref': input_ref,
            'threads': 4
        }
        #expected_results = {
        #    'direct_html_link_index': 0,
        #    'file_links': ['CheckM_summary_table.tsv.zip', 'plots.zip', 'full_output.zip'],
        #    'html_links': [
        #        'CheckM_Plot.html'
        #    ],
        #}
        result = self.getImpl().run_microtrait(self.getContext(), params)[0]

    # Test 4: single assembly from KBase
    #
    # Uncomment to skip this test
    @unittest.skip("skipped test_run_microtrait_app_single_assembly_fromref")
    def test_run_microtrait_app_single_assembly_fromref(self):
        method_name = 'test_run_microtrait_app_single_assembly_fromref'
        print ("\n=================================================================")
        print ("RUNNING "+method_name+"()")
        print ("=================================================================\n")

        #assembly_util = AssemblyUtil(self.callback_url)
        #fastas = assembly_util.get_fastas({'ref_lst': [KB_ASSEMBLY_INPUT_REF]})
        
        # run microtrait app on a single assembly
        input_ref = TEST_DATA_OBJECTS['assembly_objects'][0]
        params = {
            'workspace_name': self.ws_info[1],
            'input_ref': input_ref,
            'threads': 4
        }
        #expected_results = {
        #    'direct_html_link_index': 0,
        #    'file_links': ['CheckM_summary_table.tsv.zip', 'plots.zip', 'full_output.zip'],
        #    'html_links': [
        #        'CheckM_Plot.html'
        #    ],
        #}
        result = self.getImpl().run_microtrait(self.getContext(), params)[0]       

    # Test 5: single assembly from KBase
    #
    # Uncomment to skip this test
    @unittest.skip("skipped test_run_microtrait_app_single_assemblySet_fromref")
    def test_run_microtrait_app_single_assemblySet_fromref(self):
        method_name = 'test_run_microtrait_app_single_assemblySet_fromref'
        print ("\n=================================================================")
        print ("RUNNING "+method_name+"()")
        print ("=================================================================\n")

        #assembly_util = AssemblyUtil(self.callback_url)
        #fastas = assembly_util.get_fastas({'ref_lst': [KB_ASSEMBLY_INPUT_REF]})
        
        # run microtrait app on a single assembly
        input_ref = TEST_DATA_OBJECTS['assemblyset_object'][0]
        params = {
            'workspace_name': self.ws_info[1],
            'input_ref': input_ref,
            'threads': 4
        }
        #expected_results = {
        #    'direct_html_link_index': 0,
        #    'file_links': ['CheckM_summary_table.tsv.zip', 'plots.zip', 'full_output.zip'],
        #    'html_links': [
        #        'CheckM_Plot.html'
        #    ],
        #}
        result = self.getImpl().run_microtrait(self.getContext(), params)[0]       

    # Test 6: single assembly from KBase
    #
    # Uncomment to skip this test
    # @unittest.skip("skipped test_run_microtrait_app_single_genomeSet_fromref")
    def test_run_microtrait_app_single_genomeSet_fromref(self):
        method_name = 'test_run_microtrait_app_single_genomeSet_fromref'
        print ("\n=================================================================")
        print ("RUNNING "+method_name+"()")
        print ("=================================================================\n")

        #assembly_util = AssemblyUtil(self.callback_url)
        #fastas = assembly_util.get_fastas({'ref_lst': [KB_ASSEMBLY_INPUT_REF]})
        
        # run microtrait app on a single assembly
        input_ref = TEST_DATA_OBJECTS['genomeset_object_small'][0]
        params = {
            'workspace_name': self.ws_info[1],
            'input_ref': input_ref,
            'threads': 4
        }
        #expected_results = {
        #    'direct_html_link_index': 0,
        #    'file_links': ['CheckM_summary_table.tsv.zip', 'plots.zip', 'full_output.zip'],
        #    'html_links': [
        #        'CheckM_Plot.html'
        #    ],
        #}
        result = self.getImpl().run_microtrait(self.getContext(), params)[0]       

    def run_and_check_report(self, params, expected=None, with_filters=False):
        '''
        Run 'run_checkM_lineage_wf' with or without filters, and check the resultant KBaseReport
        using check_report()

        Args:

          params        - dictionary of input params
          expected      - dictionary representing the expected structure of the KBaseReport object
          with_filters  - whether or not to use the 'withFilter' version of the workflow

        '''

        result = self.getImpl().run_checkM_lineage_wf(self.getContext(), params)[0]

        return self.check_report(result, expected)

    # NOTE: According to Python unittest naming rules test method names should start from 'test'. # noqa
    @unittest.skip("skipped test_your_method")
    def test_your_method(self):
        # Prepare test objects in workspace if needed using
        # self.getWsClient().save_objects({'workspace': self.getWsName(),
        #                                  'objects': []})
        #
        # Run your method by
        # ret = self.getImpl().your_method(self.getContext(), parameters...)
        #
        # Check returned data with
        # self.assertEqual(ret[...], ...) or other unittest methods
        #ret = self.serviceImpl.run_kb_microtrait(self.ctx, {'workspace_name': self.wsName,
        #                                                     'parameter_1': 'Hello World!'})
        print("Running test\n")