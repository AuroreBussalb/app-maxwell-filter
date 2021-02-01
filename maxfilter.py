#!/usr/local/bin/python3

import json
import mne
import warnings

# Print mne version
print(mne.__version__)

# Generate a json.product to display messages on Brainlife UI
dict_json_product = {'brainlife': []}

# Load inputs from config.json
with open('config.json') as config_json:
    config = json.load(config_json)

# Read the files
data_file = str(config.pop('input_raw'))
raw = mne.io.read_raw_fif(data_file, allow_maxshield=True)

# Read the calibration files
cross_talk_file = config.pop('input_cross_talk')
if cross_talk_file is not None:
    cross_talk_file = str(cross_talk_file)

calibration_file = config.pop('input_calibration')
if calibration_file is not None:
    calibration_file = str(calibration_file)

# Head pos file
head_pos_file = config.pop('head_pos')
if head_pos_file is not None:
    head_pos_file = mne.chpi.read_head_pos(str(head_pos_file))

# Warning if bad channels are empty
if raw.info['bads'] is None:
    UserWarning_message = f'No channels are marked as bad. ' \
                      f'Make sure to check (automatically or visually) for bad channels before ' \
                      f'running MaxFilter.'
    warnings.warn(UserWarning_message)
    dict_json_product['brainlife'].append({'type': 'warning', 'msg': UserWarning_message})

# Check if MaxFilter was already applied on the data
sss_info = raw.info['proc_history'][0]['max_info']['sss_info']
tsss_info = raw.info['proc_history'][0]['max_info']['max_st']
if bool(sss_info) or bool(tsss_info) is True:
    ValueError_message = f'You cannot apply MaxFilter if data have already ' \
                     f'processed with Maxwell-filter.'
    # Add message to product.json and write it before raising the exception
    dict_json_product['brainlife'].append({'type': 'error', 'msg': ValueError_message})
    with open('product.json', 'w') as outfile:
        json.dump(dict_json_product, outfile)
    # Raise exception
    raise ValueError(ValueError_message)

# Apply MaxFilter
raw_maxfilter = mne.preprocessing.maxwell_filter(raw, calibration=calibration_file, cross_talk=cross_talk_file,
                                                 head_pos=head_pos_file, **config['params_maxwell_filter'])

# Save file
type_maxfilter = config.pop('params_maxwell_filter')
if type_maxfilter['st_duration'] is None:
    raw_maxfilter.save(raw_maxfilter.filenames[0].replace('.fif', '_%s.fif' % config['output_tag_sss']),
                       **config['params_save'])
else:
    raw_maxfilter.save(raw_maxfilter.filenames[0].replace('.fif', '_%s.fif' % config['output_tag_tsss']),
                       **config['params_save'])

# Create a report

# Plot MEG signals in temporal domain
fig_raw = raw.pick(['meg']).plot(duration=2, butterfly=True)
fig_raw_maxfilter = raw_maxfilter.pick(['meg']).plot(duration=2, butterfly=True)

# Plot MEG signals in frequency domain
fig_raw_psd = raw.plot_psd()
fig_raw_maxfilter_psd = raw_maxfilter.plot_psd()

report = mne.Report(verbose=True)
report.add_figs_to_section(fig_raw, captions='MEG signals before MaxFilter')
report.add_figs_to_section(fig_raw_maxfilter, captions='MEG signals after MaxFilter')
report.add_figs_to_section(fig_raw_psd, captions='Power spectral density before MaxFilter')
report.add_figs_to_section(fig_raw_maxfilter_psd, captions='Power spectral density after MaxFilter')
report.save('report_maxfilter.html', overwrite=True)

# Save the dict_json_product in a json file
with open('product.json', 'w') as outfile:
    json.dump(dict_json_product, outfile)


