/*
A KBase module: kb_microtrait
*/

module kb_microtrait {
    /*
    A boolean - 0 for false, 1 for true.
        @range (0, 1)
    */
    typedef int boolean;

    /* An X/Y/Z style reference
       e.g. "WS_ID/OBJ_ID/VER"
    */
    typedef string obj_ref;

    /* the FASTA extension
       e.g. ".fna"
    */
    typedef string FASTA_format;


    typedef structure {
        string report_name;
        string report_ref;
    } ReportResults;

    /*
        This example function accepts any number of parameters and returns results in a KBaseReport
    */
    funcdef run_kb_microtrait(mapping<string,UnspecifiedObject> params) returns (ReportResults output) authentication required;

    /*
        input_ref - reference to the input Assembly, AssemblySet, Genome, GenomeSet, or BinnedContigs data
    */
    typedef structure {
        string dir_name;    /* for use in tests */

        string input_ref;
        string workspace_name;

        string output_directory;
        string dataset_name;
        int number_of_cores;
    } microtraitParams;

    typedef structure {
        string report_name;
        string report_ref;
    } microtraitResult;

    funcdef run_microtrait(microtraitParams params)
        returns (microtraitResult result) authentication required;

};
