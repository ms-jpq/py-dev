#!/usr/bin/env perl

our $projectroot = "{{ TOP_LEVEL }}";
our $git_temp = "{{ TMP }}";
our $projects_list = $projectroot;

$feature{'remote_heads'}{'default'} = [1];
