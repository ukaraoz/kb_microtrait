/*
A KBase module: kb_microtrait
*/

module kb_microtrait {
    typedef structure {
        string report_name;
        string report_ref;
    } ReportResults;

    /*
        This example function accepts any number of parameters and returns results in a KBaseReport
    */
    funcdef run_kb_microtrait(mapping<string,UnspecifiedObject> params) returns (ReportResults output) authentication required;

};
