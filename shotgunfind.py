import glob
import os
import shutil, errno
import shotgun_api3
import clartoons_api 


sg = shotgun_api3.Shotgun(clartoons_api.url, 
                          script_name= clartoons_api.script_name,
                          api_key=clartoons_api.api_key)

#project_name = 'Worry Eaters' # id = 88
#episode_name = 'e00_test'
#episode_name = 'e01_RememberMe' #this also needs user input
sg_assets = sg.find('Asset', [['project.Project.id', 'is', 88], ['episodes.Episode.code', 'is', episode_name]], ['code', 'sg_published_files'])
assets_files_list = []
assets_path_list = []


delivery_dst = os.path.normpath("Z:/Users/Elaine/test_script/") #this needs to be user set and check this exists, defaults to "/worry_eaters/deliverable/ToAnimationTeam"


def find_latest_asset_publish():
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
def find_and_copy_asset_path():		
	for asset in assets_files_list:
		assets = sg.find('PublishedFile',[['id', 'is', asset['asset_latest_publish_id']]], ['name', 'path', 'path_cache'] )
		for j in assets:
			src =  os.path.normpath(os.path.join("Z:/Projects/" +  j['path_cache']))
			dst_dir = os.path.normpath(os.path.join(delivery_dst, os.path.dirname(j['path_cache'])))
			print dst_dir
			if not os.path.exists(dst_dir):
				os.makedirs(dst_dir)
			else:
				continue
			shutil.copy2(src, dst_dir)

def find_and_copy_episode_path(episode_name):
	episode_path_list = []
	episode_prefix, episode_suffix = episode_name.split('_')
	episode_prefix = episode_prefix.upper()
	if episode_prefix == 'E00':
		episode_name = 'e00'
		episode_prefix = episode_prefix.lower()
	episode_path = os.path.normpath(os.path.join('Z:/Projects/worry_eaters/episodes', episode_name))
	print episode_path
	
	#Copy Audio Path and files 
	audio_path = os.path.join(episode_path, 'Audio', 'WAVs')
	_, audio_rel_path = audio_path.split('Z:\Projects\\')
	dst_audio_path = os.path.normpath(os.path.join(delivery_dst, 'worry_eaters/episodes', episode_name, 'Audio', 'WAVs'))
	if not os.path.exists(dst_audio_path):
		os.makedirs(dst_audio_path)
	for root, dirs, files in os.walk(audio_path):
		for file in files: 
			path_file = os.path.join(root, file)
			shutil.copy2(path_file, dst_audio_path)
	print dst_audio_path
	#Find episode sequence and copy files
	for item in os.listdir(episode_path):
		if os.path.isdir(os.path.join(episode_path, item)):
			if episode_prefix in item: 
				episode_path_list.append(os.path.join(episode_path, item))

	for episode_path in episode_path_list: 
		for root, dirs, files in os.walk(episode_path):
			for name in dirs:
				if episode_prefix in name:
					episode_seq_path = os.path.join(episode_path, name) 
					print episode_seq_path
					episode_seq_anim = os.path.join(episode_seq_path, 'anim', 'work', 'maya')
					episode_seq_lay =  os.path.join(episode_seq_path, 'lay', 'publish', 'maya')
					episode_seq_lay_maya = os.path.join(episode_seq_lay, "*.ma")
					list_of_files = glob.glob(episode_seq_lay_maya)
					latest_lay_file = ""
					if len(list_of_files) > 1: 
						latest_lay_file = max(list_of_files, key=os.path.getctime)
					elif len(list_of_files) == 1:
						latest_lay_file = list_of_files[0]
					_, _dst_episode_seq_lay = episode_seq_lay.split('Z:\Projects\\')
					dst_episode_seq_lay = os.path.normpath(os.path.join(delivery_dst, _dst_episode_seq_lay))
					if not os.path.exists(dst_episode_seq_lay):
						os.makedirs(dst_episode_seq_lay)
					if not os.listdir(episode_seq_lay) == []:
						shutil.copy2(latest_lay_file, dst_episode_seq_lay)
					print dst_episode_seq_lay
					_, _dst_episode_seq_anim = episode_seq_anim.split('Z:\Projects\\')
					dst_episode_seq_anim = os.path.normpath(os.path.join(delivery_dst, _dst_episode_seq_anim))
					print dst_episode_seq_anim
					episode_seq_anim_maya = os.path.join(episode_seq_anim, 'workspace.mel')
					if not os.path.exists(dst_episode_seq_anim):
						os.makedirs(dst_episode_seq_anim)
					if not os.listdir(os.path.normpath(episode_seq_anim)) == []:
						shutil.copy2(episode_seq_anim_maya, dst_episode_seq_anim)

def main():
	find_latest_asset_publish()
	find_and_copy_asset_path()
	find_and_copy_episode_path(episode_name)

#destination_path = R'Z:\Projects\worry_eaters\deliverables\\'



	