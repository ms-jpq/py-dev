#!/usr/bin/env perl

our $projectroot = "{{ TOP_LEVEL }}";
our $git_temp = "{{ TMP }}";
our $projects_list = $projectroot;

# ADDN
our $prevent_xss = !0;
our $fallback_encoding = "utf-16";
our $site_name = "{{ TITLE }}";

$feature{'remote_heads'}{'default'} = [1];
