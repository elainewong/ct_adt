import os
import shutil, errno
import shotgun_api3
import clartoons_api 


sg = shotgun_api3.Shotgun(clartoons_api.url, 
                          script_name= clartoons_api.script_name,
                          api_key=clartoons_api.api_key)

project_name = 'Worry Eaters' # id = 88
episode_name = 'e00_test'
#episode_name = 'e01_RememberMe'
sg_assets = sg.find('Asset', [['project.Project.id', 'is', 88], ['episodes.Episode.code', 'is', episode_name]], ['code', 'sg_published_files',])

assets_files_list = []
for asset in sg_assets:
	published_file_id = 0
	name= ''
	for published_files in asset['sg_published_files']:
		if published_file_id  < published_files['id']:
			published_file_id  = published_files['id']
			name = published_files['name']
	assets_files_list.append({
								'name': name, 
								'asset_latest_publish_id': published_file_id}
							)

assets_path_list = []
for i in assets_files_list:
	assets = sg.find('PublishedFile',[['id', 'is', i['asset_latest_publish_id']]], ['name', 'path', 'path_cache'] )
	for j in assets: 
		print j['path']['local_path_windows']



#destination_path = R'Z:\Projects\worry_eaters\deliverables\\'


