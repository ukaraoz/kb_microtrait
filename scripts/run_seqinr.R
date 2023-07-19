#!/usr/bin/env Rscript

suppressPackageStartupMessages(library(argparser))
suppressWarnings(suppressMessages(library(parallel)))
suppressWarnings(suppressMessages(library(seqinr)))
suppressMessages(library(ggplot2))
suppressMessages(library(here))


# create parser object

parser <- arg_parser(description = "Runs seqinr to filter by length.", 
                     name = "run_seqinr",
                     hide.opts = TRUE)
parser <- add_argument(parser, "genome_fasta_files", type = "character", help = "input file of fasta paths for genomes")
parser <- add_argument(parser, "output_directory", type = "character", help = "output directory")
parser <- add_argument(parser, "dataset_name", type = "character", default = "microtrait", help = "dataset name")
parser <- add_argument(parser, "number_of_cores", type = "integer", default = 1, help = "number of cores")
#parser <- add_argument(parser, "--nguilds", type = "integer", help = "number of guilds")
parser <- add_argument(parser, "--verbose", flag = T, short = "v", help = "be verbose")
args <- parse_args(parser)

genome_fasta_files = args$genome_fasta_files
output_directory = args$output_directory
dataset = args$dataset_name
ncores = args$number_of_cores
verbose = args$verbose

#./run_seqinr.R /Users/ukaraoz/Work/kbase/microtrait_wrapper/data/assemblies_filepaths.txt \
#/Users/ukaraoz/Work/kbase \
#test 4

getmeanLength_fromfasta = function(fasta_infile) {
  fasta = read.fasta(fasta_infile, as.string = T, forceDNAtolower = F)
  mean = mean(getLength(fasta))
  result = data.frame(fasta_infile, mean)
  result
}

#genome_fasta_files = "/Users/ukaraoz/Work/kbase/microtrait_wrapper/data/assemblies_filepaths.txt"
filepaths = read.table(genome_fasta_files, stringsAsFactors = F, sep = "\t")[,1]
pathsread = length(filepaths)
pathsok = length(which(file.exists(filepaths) == TRUE))

if(verbose) {
  sprintf("%s fasta files will be processed. %s doesn't exist.\n", pathsok, pathsread-pathsok)
}

#fasta_infile = "/Users/ukaraoz/Work/kbase/microtrait_wrapper/data/assemblies/GCF_000014005.1_assembly.fa"

temp =
  parallel::mclapply(1:length(filepaths),
    function(i) {
      mean = getmeanLength_fromfasta(filepaths[i])
      mean
    },
  mc.cores = ncores)

results = do.call("rbind", temp)

text_outfile = file.path(output_directory, "stats.tsv")
write.table(results, file = text_outfile, quote = F, sep = "\t", row.names = F, col.names = T)

pdf_outfile = file.path(output_directory, "stats.pdf")
p = ggplot(results, aes(x = mean)) + geom_histogram()
suppressMessages(ggsave(p, file = pdf_outfile))

