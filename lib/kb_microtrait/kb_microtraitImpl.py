# -*- coding: utf-8 -*-
#BEGIN_HEADER
import logging
import os
import json

from installed_clients.KBaseReportClient import KBaseReport

from kb_microtrait.utils.microtraitUtil import microtraitUtil
#END_HEADER


class kb_microtrait:
    '''
    Module Name:
    kb_microtrait

    Module Description:
    A KBase module: kb_microtrait
    '''

    ######## WARNING FOR GEVENT USERS ####### noqa
    # Since asynchronous IO can lead to methods - even the same method -
    # interrupting each other, you must be *very* careful when using global
    # state. A method could easily clobber the state set by another while
    # the latter method is running.
    ######################################### noqa
    VERSION = "0.0.1"
    GIT_URL = ""
    GIT_COMMIT_HASH = "297ccac4f7f2a983d2dab7a87d45d54f65e4610f"

    #BEGIN_CLASS_HEADER
    #END_CLASS_HEADER

    # config contains contents of config file in a hash or None if it couldn't
    # be found
    def __init__(self, config):
        #BEGIN_CONSTRUCTOR
        self.config = config
        self.config['SDK_CALLBACK_URL'] = os.environ['SDK_CALLBACK_URL']
        self.config['KB_AUTH_TOKEN'] = os.environ['KB_AUTH_TOKEN']
        #self.callback_url = os.environ['SDK_CALLBACK_URL']
        #self.shared_folder = config['scratch']
        logging.basicConfig(format='%(created)s %(levelname)s: %(message)s',
                            level=logging.INFO)
        #END_CONSTRUCTOR
        pass


    def run_kb_microtrait(self, ctx, params):
        """
        This example function accepts any number of parameters and returns results in a KBaseReport
        :param params: instance of mapping from String to unspecified object
        :returns: instance of type "ReportResults" -> structure: parameter
           "report_name" of String, parameter "report_ref" of String
        """
        # ctx is the context object
        # return variables are: output
        #BEGIN run_kb_microtrait
        report = KBaseReport(self.callback_url)
        report_info = report.create({'report': {'objects_created':[],
                                                'text_message': params['parameter_1']},
                                                'workspace_name': params['workspace_name']})
        output = {
            'report_name': report_info['name'],
            'report_ref': report_info['ref'],
        }
        #END run_kb_microtrait

        # At some point might do deeper type checking...
        if not isinstance(output, dict):
            raise ValueError('Method run_kb_microtrait return value ' +
                             'output is not type dict as required.')
        # return the results
        return [output]

    def run_microtrait(self, ctx, params):
        """
        :param params: instance of type "microtraitParams" (input_ref -
           reference to the input Assembly, AssemblySet, Genome, GenomeSet,
           or BinnedContigs data) -> structure: parameter "dir_name" of
           String, parameter "input_ref" of String, parameter
           "workspace_name" of String, parameter "output_directory" of
           String, parameter "dataset_name" of String, parameter
           "number_of_cores" of Long
        :returns: instance of type "microtraitResult" -> structure: parameter
           "report_name" of String, parameter "report_ref" of String
        """
        # ctx is the context object
        # return variables are: result
        #BEGIN run_microtrait

        print('--->\nRunning kb_microtrait.run_microtrait\nparams:')
        print(json.dumps(params, indent=1))

        mtu = microtraitUtil(self.config, ctx)
        result = mtu.run_microtrait(params)

        print(json.dumps(result, indent=1))
        #END run_microtrait

        # At some point might do deeper type checking...
        if not isinstance(result, dict):
            raise ValueError('Method run_microtrait return value ' +
                             'result is not type dict as required.')
        # return the results
        return [result]
    def status(self, ctx):
        #BEGIN_STATUS
        returnVal = {'state': "OK",
                     'message': "",
                     'version': self.VERSION,
                     'git_url': self.GIT_URL,
                     'git_commit_hash': self.GIT_COMMIT_HASH}
        #END_STATUS
        return [returnVal]
