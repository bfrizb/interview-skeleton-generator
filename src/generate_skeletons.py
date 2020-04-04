#!/usr/bin/env python3
import argparse
import logging
import os
import re
import subprocess
import yaml

# Constants
SNAKE_CONVENTION = "snake"
CAMEL_CONVENTION = "camel"
NAMING_CONVENTION_STRING = "naming_convention"
LANG_TO_NAMING_CONVENTION = {
    "csharp": CAMEL_CONVENTION,
    "javascript": CAMEL_CONVENTION,
    "python": SNAKE_CONVENTION,
    "ruby": SNAKE_CONVENTION,
}
NULL_STRING = "null"
LANG_TO_NULL_CONVENTION = {
    "csharp": "null",
    "javascript": "null",
    "python": "None",
    "ruby": "nil",
}
LANG_STRING = "languages"
LANG_TO_COMMENT_CHAR = {
    "csharp": "//",
    "javascript": "//",
    "python": "#",
    "ruby": "#",
}
CC_STRING = "CC"  # CC => Comment Character(s)


def read_config(config_path):
    with open(config_path, "r") as fh:
        return yaml.load(fh.read(), Loader=yaml.SafeLoader)


def get_convention_name_map(dep_subs, naming_convention):
    def custom_replace(m):
        return m.groups()[0][1].upper()

    if naming_convention == SNAKE_CONVENTION:
        return dict()
    elif naming_convention == CAMEL_CONVENTION:
        sub_map = {}
        for orig_name in dep_subs:
            new_name = re.sub("(_[a-z])", custom_replace, orig_name)
            sub_map[orig_name] = new_name
        return sub_map
    else:
        raise ValueError(
            'Unrecognized naming convention: "{}"'.format(naming_convention)
        )


def get_lang_specific_attribute(attrib_key, attrib_map, lang, config_dict):
    attrib_value = config_dict[LANG_STRING][lang].get(attrib_key)
    if not attrib_value:
        attrib_value = attrib_map.get(lang.lower())
    if not attrib_value:
        raise RuntimeError(
            'Need a "{}"-type specified for language "{}"'.format(attrib_key, lang)
        )
    return attrib_value


def create_from_templates(config_dict):
    convention_dep_subs = config_dict.get("style_adjustments", [])
    template_files = {k: v.get("filename") for k, v in config_dict[LANG_STRING].items()}

    for lang in config_dict[LANG_STRING]:
        basename = template_files[lang]
        if basename is None:
            continue
        try:
            no_ext, ext = os.path.splitext(basename)
            with open(
                os.path.join(
                    config_dict["template_dir"], "{}_template{}".format(no_ext, ext)
                ),
                "r",
            ) as fh:
                template_contents = fh.read()
        except OSError as e:
            logging.exception(e)

        mod_contents = template_contents
        all_subs = config_dict.get("token_subs", {})

        # Update the substitution map (all_subs) after determining language specific attributes
        comment_char = get_lang_specific_attribute(
            CC_STRING, LANG_TO_COMMENT_CHAR, lang, config_dict
        )
        null_name = get_lang_specific_attribute(
            NULL_STRING, LANG_TO_NULL_CONVENTION, lang, config_dict
        )
        all_subs.update({CC_STRING: comment_char, NULL_STRING: null_name})
        # Surround all substitution keys with curly braces, and remove
        # trailing newline from substitution values
        all_subs = {"<{}>".format(k): v.rstrip("\n") for k, v in all_subs.items()}

        # Add in style adjustments based on language-specific naming conventions
        naming_convention = get_lang_specific_attribute(
            NAMING_CONVENTION_STRING, LANG_TO_NAMING_CONVENTION, lang, config_dict
        )
        all_subs.update(get_convention_name_map(convention_dep_subs, naming_convention))

        for __ in range(2):  # Run twice to resolve nested subs
            for orig_str in all_subs:
                if isinstance(all_subs[orig_str], str):
                    mod_contents = mod_contents.replace(
                        orig_str, str(all_subs[orig_str])
                    )
                elif isinstance(all_subs[orig_str], dict):
                    mod_contents = mod_contents.replace(
                        orig_str, str(all_subs[orig_str][lang])
                    )

        try:
            os.makedirs(os.path.join(config_dict["dest_dir"], lang))
        except OSError:
            pass
        with open(os.path.join(config_dict["dest_dir"], lang, basename), "w") as fh:
            fh.write(mod_contents)


def test_skeletons(config_dict):
    skeleton_files = {k: v.get("filename") for k, v in config_dict[LANG_STRING].items()}
    run_cmd = {k: v.get("run_cmd") for k, v in config_dict[LANG_STRING].items()}

    for lang in skeleton_files:
        if run_cmd[lang] is None:
            logging.warn("Skipping testing: {}".format(skeleton_files[lang]))
            continue
        full_path = os.path.join(config_dict["dest_dir"], lang, skeleton_files[lang])
        cmds = (
            run_cmd[lang]
            .replace("<FILE>", full_path)
            .replace("{dest_dir}", config_dict["dest_dir"])
            .replace("{lang}", lang)
        )
        p = subprocess.Popen(
            cmds, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        out, err = p.communicate()
        logging.info(
            "*** {lang} ***"
            "\nSTDOUT: {stdout}"
            "\nSTDERR: {stderr}"
            "\nRETURN CODE: {returncode}"
            "\n{divider}".format(
                lang=lang,
                stdout=out.decode("utf-8") if out else "<EMPTY>",
                stderr=err.decode("utf-8") if err else "<EMPTY>",
                returncode=p.returncode,
                divider="-" * 50,
            )
        )


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("config_path", help="Path to yaml config file")
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Increases the logging level of the program from INFO to DEBUG.",
    )
    return parser.parse_args()


def main(args):
    logging.basicConfig(
        format=("[%(levelname)s Message] %(message)s"),
        level=logging.DEBUG if args.verbose else logging.INFO,
    )
    config_dict = read_config(args.config_path)
    try:
        os.mkdir(config_dict["dest_dir"])
    except OSError:
        pass
    create_from_templates(config_dict)
    test_skeletons(config_dict)


if __name__ == "__main__":
    main(parse_args())
