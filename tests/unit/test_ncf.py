#!/usr/bin/env python

import unittest
import ncf
import os.path
import subprocess
import shutil

class TestNcf(unittest.TestCase):

  def setUp(self):
    self.test_technique_file = os.path.realpath('test_technique.cf')
    self.test_generic_method_file = 'test_generic_method.cf'
    self.technique_content = open(self.test_technique_file).read()
    self.generic_method_content = open(self.test_generic_method_file).read()
    
    self.technique_metadata = ncf.parse_technique_metadata(self.technique_content)
    method_calls = ncf.parse_technique_methods(self.test_technique_file)
    self.technique_metadata['method_calls'] = method_calls

  def test_get_ncf_root_dir(self):
    self.assertEquals(ncf.get_root_dir(), os.path.realpath(os.path.dirname(os.path.realpath(__file__)) + "/../../"))

  #####################################
  # Generic tests for parsing .cf files
  #####################################

  def test_parse_bundlefile_empty(self):
    """Attempting to parse an empty string should raise an exception"""
    self.assertRaises(Exception, ncf.parse_bundlefile_metadata, "")

  def test_parse_bundlefile_incomplete(self):
    """Attempting to parse a bundle file with metadata after the bundle agent declaration should raise an exception"""
    self.assertRaises(Exception, ncf.parse_bundlefile_metadata, """# @name A name
                                      bundle agent thingy {
                                      }
                                      # @description bla bla
                                      # @version 1.0""")

  #########################
  # Technique parsing tests
  #########################

  def test_parse_technique(self):
    """Parsing should return a dict with all defined technique tags"""
    metadata = ncf.parse_technique_metadata(self.technique_content)
    self.assertEqual(sorted(metadata.keys()), sorted(ncf.tags["technique"]+ncf.tags["common"]))

  def test_parse_technique_data(self):
    """Parsing should return a dict with the data from the test technique"""
    metadata = ncf.parse_technique_metadata(self.technique_content)
    self.assertEqual(metadata['name'], "Bla Technique for evaluation of parsingness")
    self.assertEqual(metadata['description'], "This meta-Technique is a sample only, allowing for testing.")
    self.assertEqual(metadata['version'], "0.1")
    self.assertEqual(metadata['bundle_name'], "bla")
    self.assertEqual(metadata['bundle_args'], [])

  ##############################
  # Generic method parsing tests
  ##############################

  def test_parse_generic_method(self):
    """Parsing a generic method should return a dict with all defined generic_method tags"""
    metadata = ncf.parse_generic_method_metadata(self.generic_method_content)
    self.assertEqual(sorted(metadata.keys()), sorted(ncf.tags["generic_method"]+ncf.tags["common"]))

  def test_parse_generic_method_data(self):
    """Parsing should return a dict with the data from the test generic_method"""
    metadata = ncf.parse_generic_method_metadata(self.generic_method_content)
    self.assertEqual(metadata['bundle_name'], "package_install_version")
    self.assertEqual(metadata['bundle_args'], ["package_name", "package_version"])
    self.assertEqual(metadata['name'], "Package install")
    self.assertEqual(metadata['description'], "Install a package by name from the default system package manager")
    self.assertEqual(metadata['parameter'], [{'name': 'package_name', 'description': 'Name of the package to install'},{'name': 'package_version', 'description': 'Version of the package to install'}])
    self.assertEqual(metadata['class_prefix'], "package_install")
    self.assertEqual(metadata['class_parameter'], "package_name")
    self.assertEqual(metadata['class_parameter_id'], 1)
    self.assertEqual(len(metadata), len(ncf.tags["generic_method"]+ncf.tags["common"]))

  ###########################################################
  # Tests to obtain the generic methods that a Technique uses
  ###########################################################

  def test_parse_technique_generic_method_calls_nonexistant_file(self):
    """Attempting to parse a non existant file should return an exception"""
    self.assertRaises(Exception, ncf.parse_technique_methods, "/dev/nonexistant")

  def test_parse_technique_generic_method_calls(self):
    """Parsing a technique should return a list of it's generic method calls"""
    bundle_calls = ncf.parse_technique_methods(self.test_technique_file)
    expected = [  { 'method_name': 'package_install_version', 'args': ['${bla.apache_package_name}', '2.2.11'], 'class_context': 'any' },
                  { 'method_name': 'service_start', 'args': ['${bla.apache_package_name}'], 'class_context': 'cfengine' },
                  { 'method_name': 'package_install', 'args': ['openssh-server'], 'class_context': 'cfengine' },
                  { 'method_name': '_logger', 'args': ['NA', 'NA'], 'class_context': '!cfengine' },
               ]
    self.assertEqual(bundle_calls, expected)

  def test_parse_technique_generic_method_calls_strings(self):
    """Parsing a technique should return a list of it's generic method calls even if they are string literals"""
    bundle_calls = ncf.parse_technique_methods(self.test_technique_file)
    expected = [  { 'method_name': 'package_install_version', 'args': ['${bla.apache_package_name}', '2.2.11'], 'class_context': 'any' },
                  { 'method_name': 'service_start', 'args': ['${bla.apache_package_name}'], 'class_context': 'cfengine' },
                  { 'method_name': 'package_install', 'args': ['openssh-server'], 'class_context': 'cfengine' },
                  { 'method_name': '_logger', 'args': ['NA', 'NA'], 'class_context': '!cfengine' },
               ]
    self.assertEqual(bundle_calls, expected)

  #####################################
  # Tests for reading all metadata info
  #####################################

  def test_get_all_generic_methods_filenames(self):
    """test_get_all_generic_methods_filenames should return a list of all generic_methods files"""
    base_dir = ncf.get_root_dir() + "/tree/30_generic_methods"
    alternative_path = os.path.dirname(os.path.realpath(__file__)) + "/test_methods"

    # Get list of generic_methods without prefix "_" on the filesystem
    list_methods_files = []
    ## Get recursivly each promises in the basic path and the alternative one
    list_methods_files += [os.path.join(full_path,filename) for full_path, dirname, files in os.walk(base_dir) for filename in files if not filename.startswith('_') and filename.endswith('.cf')]
    list_methods_files += [os.path.join(full_path,filename) for full_path, dirname, files in os.walk(alternative_path+"/30_generic_methods") for filename in files if not filename.startswith('_') and filename.endswith('.cf')]

    filenames = ncf.get_all_generic_methods_filenames(alternative_path)

    filenames.sort()
    list_methods_files.sort()

    self.assertEquals(filenames, list_methods_files)

  def test_get_all_techniques_filenames(self):
    """test_get_all_techniques_filenames should return a list of all techniques files"""
    base_dir = ncf.get_root_dir() + "/tree/50_techniques"
    alternative_path = os.path.dirname(os.path.realpath(__file__)) + "/test_methods"

    # Get list of techniques without prefix "_" on the filesystem
    list_methods_files = []
    ## Get recursivly each promises in the basic path and the alternative one
    list_methods_files += [os.path.join(full_path,filename) for full_path, dirname, files in os.walk(base_dir) for filename in files if not filename.startswith('_') and filename.endswith('.cf')]
    list_methods_files += [os.path.join(full_path,filename) for full_path, dirname, files in os.walk(alternative_path+"/50_techniques") for filename in files if not filename.startswith('_') and filename.endswith('.cf')]

    filenames = ncf.get_all_techniques_filenames(alternative_path)

    filenames.sort()
    list_methods_files.sort()

    self.assertEquals(filenames, list_methods_files)

  def test_get_all_generic_methods_metadata(self):
    """get_all_generic_methods_metadata should return a list of all generic_methods with all defined metadata tags"""
    metadata = ncf.get_all_generic_methods_metadata()

    number_generic_methods = len(ncf.get_all_generic_methods_filenames())
    self.assertEquals(number_generic_methods, len(metadata))

  def test_get_all_generic_methods_metadata_with_arg(self):
    """get_all_generic_methods_metadata should return a list of all generic_methods with all defined metadata tags"""
    alternative_path = os.path.dirname(os.path.realpath(__file__)) + "/test_methods"
    metadata = ncf.get_all_generic_methods_metadata(alternative_path)

    number_generic_methods = len(ncf.get_all_generic_methods_filenames(alternative_path))
    self.assertEquals(number_generic_methods, len(metadata))

  def test_get_all_techniques_metadata(self):
    """get_all_techniques_metadata should return a list of all techniques with all defined metadata tags and methods_called"""
    metadata = ncf.get_all_techniques_metadata()

    number = len(ncf.get_all_techniques_filenames())
    self.assertEquals(number, len(metadata))

  def test_get_all_techniques_metadata_with_args(self):
    """get_all_techniques_metadata should return a list of all techniques with all defined metadata tags and methods_called"""
    alternative_path = os.path.dirname(os.path.realpath(__file__)) + "/test_methods"
    metadata = ncf.get_all_techniques_metadata(alt_path=alternative_path)

    number = len(ncf.get_all_techniques_filenames(alternative_path))
    self.assertEquals(number, len(metadata))
    
  #####################################
  # Tests for writing/delete Techniques all metadata info
  #####################################
    
  def test_generate_technique_content(self):
    """Test if content from a valid technique generated a valid CFEngine file as expected"""
    # Expected content of Technique
    expected_result = []
    expected_result.append('# @name Bla Technique for evaluation of parsingness')
    expected_result.append('# @description This meta-Technique is a sample only, allowing for testing.')
    expected_result.append('# @version 0.1')
    expected_result.append('')
    expected_result.append('bundle agent bla')
    expected_result.append('{')
    expected_result.append('  methods:')
    expected_result.append('    "method_call" usebundle => package_install_version("${bla.apache_package_name}", "2.2.11"),')
    expected_result.append('      ifvarclass => "any";')

    expected_result.append('    "method_call" usebundle => service_start("${bla.apache_package_name}"),')
    expected_result.append('      ifvarclass => "cfengine";')

    expected_result.append('    "method_call" usebundle => package_install("openssh-server"),')
    expected_result.append('      ifvarclass => "cfengine";')

    expected_result.append('    "method_call" usebundle => _logger("NA", "NA"),')
    expected_result.append('      ifvarclass => "!cfengine";')
    expected_result.append('}')

    # Join all lines with \n to get a pretty technique file
    result = '\n'.join(expected_result)+"\n"
    generated_result = ncf.generate_technique_content(self.technique_metadata)

    self.assertEquals(result, generated_result)

  def test_check_mandatory_keys_technique_metadata(self):
    """Test if a broken metadata raise a correct NcfError exception"""

    broken_metadata = { "description": "test", "version" : "test" }

    self.assertRaises(ncf.NcfError, ncf.check_technique_metadata, broken_metadata)

  def test_check_nonempty_keys_technique_metadata(self):
    """Test if a broken metadata raise a correct NcfError exception"""

    broken_metadata = { "name": "", "bundle_name" : "", "method_calls" : [] }

    self.assertRaises(ncf.NcfError, ncf.check_technique_metadata, broken_metadata)


  def test_add_default_values_technique_metadata(self):
    """Test if a missing data in technique metadata are correctly replaced with default values"""

    default_metadata = { "name": "test", "bundle_name" : "test", "method_calls" : [ { "method_name" : "test"}] }
    technique = ncf.add_default_values_technique_metadata(default_metadata)

    result = technique['description'] == "" and technique['version'] == "1.0"

    self.assertTrue(result)

  def test_check_mandatory_keys_method_call(self):
    """Test if a broken metadata raise a correct NcfError exception"""

    broken_method_call = { "class_context": "test" }

    self.assertRaises(ncf.NcfError, ncf.check_technique_method_call, broken_method_call)

  def test_check_nonempty_keys_method_call(self):
    """Test if a broken metadata raise a correct NcfError exception"""

    broken_method_call = { "method_name": "" }

    self.assertRaises(ncf.NcfError, ncf.check_technique_method_call, broken_method_call)


  def test_add_default_values_method_call(self):
    """Test if a missing data in technique metadata are correctly replaced with default values"""

    default_method_call = { "class_context": ""}
    technique = ncf.add_default_values_technique_method_call(default_method_call)

    result = technique['class_context'] == "any"

    self.assertTrue(result)

  def test_write_technique(self):
    """Check if a technique file is written in the correct path from its metadata"""
    ncf.write_technique(self.technique_metadata, os.path.realpath("write_test"))
    result = os.path.exists(os.path.realpath(os.path.join("write_test", "50_techniques", self.technique_metadata['bundle_name'], self.technique_metadata['bundle_name']+".cf")))
    # Clean
    shutil.rmtree(os.path.realpath(os.path.join("write_test", "50_techniques")))
    self.assertTrue(result)
    
  def test_delete_technique(self):
    """Check if a technique file is correctly deleted"""
    ncf.write_technique(self.technique_metadata, os.path.realpath("write_test"))
    ncf.delete_technique(self.technique_metadata['bundle_name'], os.path.realpath("write_test"))
    result = not os.path.exists(os.path.realpath(os.path.join("write_test", "50_techniques", self.technique_metadata['bundle_name'])))
    # Clean
    shutil.rmtree(os.path.realpath(os.path.join("write_test", "50_techniques")))
    self.assertTrue(result)
    
  #####################################
  # Tests for detecting hooks
  #####################################

  def test_pre_hooks(self):
    pre_hooks = ncf.get_hooks("pre", "delete_technique", os.path.realpath("test_hooks/hooks.d"))
    expect = [ "pre.delete_technique.commit.rpmsave.sh", "pre.delete_technique.commit.sh" ]
    assert pre_hooks == expect

  def test_post_hooks(self):
    post_hooks = ncf.get_hooks("post",  "(write|create)_technique", "test_hooks/hooks.d")
    expect = [ "post.create_technique.commit.exe", "post.write_technique.commit.sh" ]
    assert post_hooks == expect

if __name__ == '__main__':
  unittest.main()
