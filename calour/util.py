# ----------------------------------------------------------------------------
# Copyright (c) 2016--,  Calour development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
# ----------------------------------------------------------------------------

from logging import getLogger
import hashlib
import configparser
from pkg_resources import resource_filename
import scipy

logger = getLogger(__name__)


def get_fields(exp):
    '''
    return the sample fields of an experiment
    '''
    return list(exp.sample_metadata.columns)


def get_field_vals(exp, field, unique=True):
    '''
    return the values in sample field (unique or all)
    '''
    vals = exp.sample_metadata[field]
    if unique:
        vals = list(set(vals))
    return vals


def _get_taxonomy_string(exp, separator=';', remove_underscore=True, to_lower=False):
    '''Get a nice taxonomy string
    Convert the taxonomy list stored (from biom.read_table) to a single string per feature

    Parameters
    ----------
    exp : Experiment
        with the taxonomy entry in the feature_metadata
    separator : str (optional)
        the output separator to use between the taxonomic levels
    remove_underscore : bool (optional)
        True (default) to remove the 'g__' entries and missing values
        False to keep them
    to_lower : bool (optional)
        False (default) to keep case
        True to convert to lowercase

    Returns
    -------
    taxonomy : list of str
        list of taxonomy string per feature
    '''
    # test if we have taxonomy in the feature metadata
    logger.debug('getting taxonomy string')
    if 'taxonomy' not in exp.feature_metadata.columns:
        raise ValueError('No taxonomy field in experiment')

    # if it is not a list - just return it
    if not isinstance(exp.feature_metadata['taxonomy'][0], list):
        return exp.feature_metadata['taxonomy']

    if not remove_underscore:
        taxonomy = [separator.join(x) for x in exp.feature_metadata['taxonomy']]
    else:
        taxonomy = []
        for ctax in exp.feature_metadata['taxonomy']:
            taxstr = ''
            for clevel in ctax:
                clevel = clevel.strip()
                if len(clevel) > 3:
                    if clevel[1:3] == '__':
                        clevel = clevel[3:]
                    taxstr += clevel + separator
            if len(taxstr) == 0:
                taxstr = 'na'
            taxonomy.append(taxstr)

    if to_lower:
        taxonomy = [x.lower() for x in taxonomy]
    return taxonomy


def get_file_md5(filename):
    '''get the md5 of the text file.

    Parameters
    ----------
    filename : str
        name of the file to calculate md5 on

    Returns
    -------
    flmd5: str
        the md5 of the file filename
    '''
    with open(filename, 'r') as fl:
        flmd5 = hashlib.md5()
        for cline in fl:
            try:
                flmd5.update(cline.encode('utf-8'))
            except:
                logger.warn('map md5 cannot be calculated - utf problems?')
                return ''
        flmd5 = flmd5.hexdigest()
        return flmd5


def get_data_md5(data):
    '''Calculate the md5 of a dense/sparse matrix

    Calculat matrix md5 based on row by row order

    Parameters
    ----------
    data : dense or sparse matrix

    Returns
    -------
    datmd5 : str
        the md5 of the data (row by row)
    '''
    logger.debug('caculating data md5')
    datmd5 = hashlib.md5()
    if scipy.sparse.issparse(data):
        issparse = True
    else:
        issparse = False
    for crow in range(data.shape[0]):
        if issparse:
            # if sparse need to convert to numpy array
            cdat = data[crow, :].toarray()[0]
        else:
            cdat = data[crow, :]
        # convert to string of raw data since hashlib.md5 does not take numpy array as input
        datmd5.update(cdat.tostring())

    datmd5 = datmd5.hexdigest()
    logger.debug('data md5 is: %s' % datmd5)
    return datmd5


def get_config_file():
    '''Get the calour config file location
    located in calour/config.calour.txt

    Parameters
    ----------

    Returns
    -------
    config_file_name : str
        the full path to the calour config file
    '''
    config_file_name = resource_filename(__package__, 'calour.config')
    return config_file_name


def set_config_value(key, value, section='DEFAULT', config_file_name=None):
    '''Set the value in the calour config file

    Parameters
    ----------
    key : str
        the key to get the value for
    value : str
        the value to store
    section : str (optional)
        the section to get the value from
    config_file_name : str (optional)
        the full path to the config file or None to use XXX
    '''
    if config_file_name is None:
        config_file_name = get_config_file()

    config = configparser.ConfigParser()
    config.read(config_file_name)
    if section not in config:
        config.add_section(section)
    config.set(section, key, value)
    with open(config_file_name, 'w') as config_file:
        config.write(config_file)
    logger.debug('wrote key %s value %s to config file' % (key, value))


def get_config_value(key, fallback=None, section='DEFAULT', config_file_name=None):
    '''Get the value from the calour config file

    Parameters
    ----------
    key : str
        the key to get the value for
    fallback : str (optional)
        the fallback value if the key/section/file does not exist
    section : str (optional)
        the section to get the value from
    config_file_name : str (optional)
        the full path to the config file or None to use XXX

    Returns
    -------
    value : str
        value of the key or fallback if file/section/key does not exist
    '''
    if config_file_name is None:
        config_file_name = get_config_file()

    config = configparser.ConfigParser()
    config.read(config_file_name)

    if section not in config:
        logger.debug('section %s not in config file %s' % (section, config_file_name))
        return fallback

    if key not in config[section]:
        logger.debug('key %s not in config file %s section %s' % (key, config_file_name, section))
        return fallback

    value = config[section][key]
    logger.debug('found value %s for key %s' % (value, key))
    return value
