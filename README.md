# Interview Skeleton Generator

WARNING!: This repository is very much a work-in-progress!

## Purpose

To generate interview challenge "code skeletons" for an arbitrary number of programming languages, when provided with (1) template files for each programming language, and (2) a yaml config file enumerating the substitutions and transformation to be performed on each template file.

"Code skeleton" refer to a relatively small amount of boilerplate code provided to an interview candidate as a starting point for the interview. For example, this code skeleton might include program/function inputs and expected outputs that the candidate is expected to use to validate that his/her solution is working as expected.

The intention of providing a code skeleton is save precious interview time, so that the candidate isn't wasting interview time writing out trivial but necessary code, and can instead focus on fleshing out the code skeleton with logic that addresses the meat of the matter (pun intended).

## Usage

For program usage and help: `$ python src/generate_skeletons.py -h`

Please see the files under the `examples` directory for an example of how to use this program.
