#!/usr/bin/env nextflow

raw_loc = "$base_dir/raw"
converted_loc = "$base_dir/converted"
processed_loc = "$base_dir/processed"
annotated_loc = "$base_dir/annotated"
results_loc = "$base_dir/results"

process convert{
    input:
    path raw_loc

    output:
    path converted_loc

    
}