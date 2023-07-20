# -*- coding: utf-8 -*-
import time
import os
import uuid
import subprocess
import sys
import re
import ast
import json
import shutil
from decimal import Decimal

from installed_clients.KBaseReportClient import KBaseReport
from kb_microtrait.utils.DataStagingUtils import DataStagingUtils


def log(message, prefix_newline=False):
    """Logging function, provides a hook to suppress or redirect log messages."""
    print(('\n' if prefix_newline else '') + '{0:.2f}'.format(time.time()) + ': ' + str(message))
    sys.stdout.flush()

class microtraitUtil  :
    def __init__(self, config, ctx):
        self.config = config
        self.ctx = ctx
        self.callback_url = config['SDK_CALLBACK_URL']
        #self.callback_url = os.environ['SDK_CALLBACK_URL']
        self.scratch = config['scratch']
        self.threads = config['threads']
        self.appdir = config['appdir']

    def run_microtrait(self, params):
        '''
        Main entry point for running the microtrait as a KBase App
        '''

        #print(json.dumps(self.scratch, indent=1))

        # 0) validate basic parameters
        if 'input_ref' not in params:
            raise ValueError('input_ref field was not set in params for run_microtrait')
        if 'workspace_name' not in params:
            raise ValueError('workspace_name field was not set in params for run_microtrait')

        # 1) stage input data
        self.fasta_extension = 'fna'
        #self.binned_contigs_builder_fasta_extension = 'fasta'
        dsu = DataStagingUtils(self.config, self.ctx)
        staged_input = dsu.stage_input(params['input_ref'], self.fasta_extension)
        # fasta_files_filepath is a text file with full paths to each fasta genome file
        # at this point, they should be all valid paths
        suffix = staged_input['folder_suffix']
        fasta_files_filepath = staged_input['fasta_files_filepath']

        output_dir = os.path.join(self.scratch, 'output_' + suffix)
        plots_dir = os.path.join(self.scratch, 'plot_' + suffix)
        html_dir = os.path.join(self.scratch, 'html_' + suffix)
        log('Staged file for fasta file paths: ' + fasta_files_filepath)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        if not os.path.exists(html_dir):
            os.makedirs(html_dir)

        # 2) run microtrait
        microtrait_options = {'genome_fasta_files': fasta_files_filepath,
                              'output_directory': output_dir,
                              'dataset_name': "test",
                              'number_of_cores': self.threads
                              }
        command = self.run_microtrait_local(microtrait_options)

        # 3) Package results
        shutil.copyfile(os.path.join(self.appdir, 'data/microtrait-trait_matrixatgranularity3.txt'), os.path.join(output_dir, 'microtrait-trait_matrixatgranularity3.txt'))
        shutil.copyfile(os.path.join(self.appdir, 'data/microtrait-trait_matrixatgranularity2.txt'), os.path.join(output_dir, 'microtrait-trait_matrixatgranularity2.txt'))
        shutil.copyfile(os.path.join(self.appdir, 'data/microtrait-trait_matrixatgranularity1.txt'), os.path.join(output_dir, 'microtrait-trait_matrixatgranularity1.txt'))
        shutil.copyfile(os.path.join(self.appdir, 'data/genome2guild.txt'), os.path.join(output_dir, 'genome2guild.txt'))
        shutil.copyfile(os.path.join(self.appdir, 'data/guild2traitprofilewlegend.pdf'), os.path.join(output_dir, 'guild2traitprofilewlegend.pdf'))
        shutil.copyfile(os.path.join(self.appdir, 'data/alltraits.cov.ward-ordered.nolegend.pdf'), os.path.join(output_dir, 'alltraits.cov.ward-ordered.nolegend.pdf'))
        shutil.copyfile(os.path.join(self.appdir, 'data/guildsizedist.pdf'), os.path.join(output_dir, 'guildsizedist.pdf'))
        # output_files = self._get_results_files(output_dir)
        output_files = self._get_results_files(output_dir)
        #self._write_html(os.path.join(html_dir, "microtrait.html"), 
        #                 output_files['stats_pdf']['path'])

        report_params = {'message': '',
                         'direct_html_link_index': 0,
                         'file_links': [value for key, value in output_files.items()
                                                                if value['path'] is not None],
                         'html_links': [],
                         'report_object_name': 'kb_microtrait_report_' + str(uuid.uuid4()),
                         'workspace_name': params['workspace_name']
                        }
        kr = KBaseReport(self.callback_url)
        report_output = kr.create_extended_report(report_params)

        returnVal =  {'report_name': report_output['name'],
                      'report_ref': report_output['ref']}

        return returnVal

    def run_microtrait_local(self, options):
        '''
        Build the command for the wrapper script
        '''

        #run_seqinr_options = {'genome_fasta_files': "genome_fasta_files",
        #                      'output_directory': "output_directory",
        #                      'dataset_name': "dataset_name",
        #                      'number_of_cores': 4
        #                      }
        #self.run_checkM('lineage_wf', lineage_wf_options)
        command = self._build_command(options)
        log('Running with this command: ' + ' '.join(command))
        
        log_output_file = None
        p = subprocess.Popen(command, cwd=self.scratch, shell=False)
        exitCode = p.wait()

        if log_output_file:
            log_output_file.close()
        #return command
        if (exitCode == 0):
           log('Executed command: ' + ' '.join(command) + '\n' +
               'Exit Code: ' + str(exitCode))
        else:
           raise ValueError('Error running command: ' + ' '.join(command) + '\n' +
               'Exit Code: ' + str(exitCode))

    def _get_results_files(self, output_dir, output_files = None):
        if output_files is None:
            output_files = dict()

        trait_matrixatgranularity3_loc = os.path.join(output_dir, 'microtrait-trait_matrixatgranularity3.txt')
        output_files['trait_matrixatgranularity3'] = {'path': trait_matrixatgranularity3_loc,
                                 'name': 'trait_matrixatgranularity3',
                                 'label': '',
                                 'description': ''}
        trait_matrixatgranularity2_loc = os.path.join(output_dir, 'microtrait-trait_matrixatgranularity2.txt')
        output_files['trait_matrixatgranularity2'] = {'path': trait_matrixatgranularity2_loc,
                                 'name': 'trait_matrixatgranularity2',
                                 'label': '',
                                 'description': ''}
        trait_matrixatgranularity1_loc = os.path.join(output_dir, 'microtrait-trait_matrixatgranularity1.txt')
        output_files['trait_matrixatgranularity1'] = {'path': trait_matrixatgranularity1_loc,
                                 'name': 'trait_matrixatgranularity1',
                                 'label': '',
                                 'description': ''}
        genome2guild_loc = os.path.join(output_dir, 'genome2guild.txt')
        output_files['genome2guild'] = {'path': genome2guild_loc,
                                 'name': 'genome2guild',
                                 'label': '',
                                 'description': ''}
        guild2traitprofilewlegend_loc = os.path.join(output_dir, 'guild2traitprofilewlegend.pdf')
        output_files[' guild2traitprofilewlegend'] = {'path': guild2traitprofilewlegend_loc,
                                 'name': 'guild2traitprofilewlegend',
                                 'label': '',
                                 'description': ''}
        alltraitscovariance_loc = os.path.join(output_dir, 'alltraits.cov.ward-ordered.nolegend.pdf')
        output_files[' alltraitscovariance'] = {'path': alltraitscovariance_loc,
                                 'name': 'alltraitscovariance',
                                 'label': '',
                                 'description': ''}
        guildsizedist_loc = os.path.join(output_dir, 'guildsizedist.pdf')
        output_files[' guildsizedist'] = {'path': guildsizedist_loc,
                                 'name': 'guildsizedist',
                                 'label': '',
                                 'description': ''}

        return output_files

    def _write_html(self, html_path, pdf_file):
        html_report_lines = []
        html_report_lines += ['<html>']
        html_report_lines += ['<head>']
        html_report_lines += ['<title>microTrait results</title>']
        html_report_lines += ['</head>']
        html_report_lines += ['<body>']
        html_report_lines += ['<h1>microTrait results</h1>']
        html_report_lines += ['<p><a href="' + pdf_file + '">pdf</a>.</p>']
        html_report_lines += ['</body>']
        html_report_lines += ['</html>']
        html_report_str = "\n".join(html_report_lines)
        with open(html_path, 'w') as html_handle:
                html_handle.write(html_report_str)
        return(html_report_str)
            
    def _build_command(self, options):
        command = [self.appdir + '/scripts/' + 'run_seqinr.R']
        self._validate_options(options)
        command.append(options['genome_fasta_files'])
        command.append(options['output_directory'])
        command.append(options['dataset_name'])
        command.append(options['number_of_cores'])
        return command

    def _validate_options(self, options):
        if 'genome_fasta_files' not in options:
            raise ValueError('cannot run run_seqinr ' + ' without genome_fasta_files option set')
        if 'output_directory' not in options:
            raise ValueError('cannot run run_seqinr ' + ' without output_directory option set')
        if 'dataset_name' not in options:
            raise ValueError('cannot run run_seqinr ' + ' without dataset_name option set')
        if 'number_of_cores' not in options:
            raise ValueError('cannot run run_seqinr ' + ' without number_of_cores option set')