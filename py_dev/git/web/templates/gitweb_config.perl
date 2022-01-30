#!/usr/bin/env perl

our $projectroot = "{{ TOP_LEVEL }}";
our $git_temp = "{{ TMP }}";
our $projects_list = $projectroot;

# ADDN
our $site_name = "{{ TITLE }}";

$feature{'remote_heads'}{'default'} = [1];
