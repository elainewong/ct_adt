import argparse
import glob
import os
import shutil, errno
import shotgun_api3
import clartoons_api 
import stat
from datetime import datetime
import json

sg = shotgun_api3.Shotgun(clartoons_api.url, 
                          script_name= clartoons_api.script_name,
                          api_key=clartoons_api.api_key)
 

#If no new directory, makes new direcory and copies contents to new directory
def copy_files(src, dst):
    if not os.path.exists(dst):
        os.makedirs(dst)
    shutil.copy2(src, dst)

#from https://stackoverflow.com/questions/1868714/how-do-i-copy-an-entire-directory-of-files-into-an-existing-directory-using-pyth
#copies all contents in a root folder and preserves subfolder structure
def copytree(src, dst, symlinks = False, ignore = None):
  if not os.path.exists(dst):
    os.makedirs(dst)
    shutil.copystat(src, dst)
  lst = os.listdir(src)
  if ignore:
    excl = ignore(src, lst)
    lst = [x for x in lst if x not in excl]
  for item in lst:
    s = os.path.join(src, item)
    d = os.path.join(dst, item)
    if symlinks and os.path.islink(s):
      if os.path.lexists(d):
        os.remove(d)
      os.symlink(os.readlink(s), d)
      try:
        st = os.lstat(s)
        mode = stat.S_IMODE(st.st_mode)
        os.lchmod(d, mode)
      except:
        pass # lchmod not available
    elif os.path.isdir(s):
      copytree(s, d, symlinks, ignore)
    else:
      shutil.copy2(s, d)



#Uses ShotgunAPI to look for all the assets in a specific episode and 
#finds the name, id, and latest publish of the asset
def find_latest_asset_publish(sg_assets, delivery_dst):
    assets_files_path = os.path.normpath(os.path.join(delivery_dst, 'assets.json'))
    print "finding latest assets"
    assets_files_list = []
    assets_path_list = []

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

    with open(assets_files_path, 'wb') as fp:
        json.dump(assets_files_list, fp)
    return assets_files_list

#uses the latest asset ID to find the published path and copies it to the delivery location
def find_and_copy_asset_path(delivery_dst, assets_files_list):
    print "finding and copying assets rigs and textures for deilvery"        
    for asset in assets_files_list:
        assets = sg.find('PublishedFile',[['id', 'is', asset['asset_latest_publish_id']]], ['name', 'path', 'path_cache', 'task'] )
        for j in assets:
            taskname = j['task']['name'].split('_')[-1]
            taskname = taskname.lower()
            asset_path =  os.path.dirname(j['path_cache']).split(taskname)[0]
            tex_path = os.path.normpath(os.path.join("Z:/Projects/", asset_path, 'tex'))
            dst_tex_path = os.path.normpath(os.path.join(delivery_dst, asset_path, 'tex'))
            if not os.path.exists(dst_tex_path):
                os.makedirs(dst_tex_path)
            copytree(tex_path, dst_tex_path)
            src =  os.path.normpath(os.path.join("Z:/Projects/", j['path_cache']))
            dst_dir = os.path.normpath(os.path.join(delivery_dst, os.path.dirname(j['path_cache'])))
            print src
            if not '.DS_Store' in j['path_cache']:
                copy_files(src, dst_dir)

#Finds the directory path for the episode in question
def find_and_copy_episode_path(episode_name):
    episode_path_list = []
    episode_prefix, episode_suffix = episode_name.split('_')
    episode_prefix = episode_prefix.upper()
    if episode_prefix == 'E00':
        episode_name = 'e00'
        episode_prefix = episode_prefix.lower()
    episode_path = os.path.normpath(os.path.join('Z:/Projects/worry_eaters/episodes', episode_name))
    return episode_path, episode_name, episode_prefix, episode_path_list
    


#Copy Audio Path and files 
def copy_audio_path(episode_path, episode_name, delivery_dst):
    print "finding and copying audio path for deilvery"
    audio_path = os.path.join(episode_path, 'Audio', 'WAVs')
    _, audio_rel_path = audio_path.split('Z:\Projects\\')
    dst_audio_path = os.path.normpath(os.path.join(delivery_dst, 'worry_eaters/episodes', episode_name, 'Audio', 'WAVs'))
    animatics_path = os.path.normpath(os.path.join(episode_path, 'worry_eaters/episodes', episode_name, 'Animatic'))
    dst_animatics_path = os.path.normpath(os.path.join(delivery_dst, animatics_path.split('Z:\Projects\\')[-1]))
    if not os.path.exists(dst_animatics_path):
    	os.makedirs(dst_animatics_path)
    if not os.path.exists(dst_audio_path):
        os.makedirs(dst_audio_path)
    for root, dirs, files in os.walk(audio_path):
        for file in files: 
            path_file = os.path.join(root, file)
            shutil.copy2(path_file, dst_audio_path)


#copying project episode path and copying it for delivery
def copy_anim_layout_path(episode_path, episode_prefix, episode_path_list, delivery_dst):
    print "finding and copying layout maya files for delivery"
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
                    episode_seq_anim = os.path.normpath(os.path.join(episode_seq_path, 'anim', 'work', 'maya'))
                    episode_seq_lay =  os.path.join(episode_seq_path, 'lay', 'publish', 'maya')
                    episode_seq_lay_maya = os.path.join(episode_seq_lay, "*.ma")
                    episode_seq_playblast_dir = os.path.join(episode_seq_path, 'lay', 'review')
                    dst_episode_seq_playblast_dir = os.path.normpath(os.path.join(delivery_dst, episode_seq_playblast_dir.split('Z:\Projects\\')[-1]))
                    episode_seq_lay_work = os.path.join(episode_seq_path, 'lay', 'work', 'maya')
                    copytree(episode_seq_playblast_dir, dst_episode_seq_playblast_dir)

                    list_of_files = glob.glob(episode_seq_lay_maya)
                    latest_lay_file = ""
                    if len(list_of_files) > 1: 
                        latest_lay_file = max(list_of_files, key=os.path.getctime)
                    elif len(list_of_files) == 1:
                        latest_lay_file = list_of_files[0]
                    dst_episode_seq_lay = os.path.normpath(os.path.join(delivery_dst, episode_seq_lay.split('Z:\Projects\\')[-1]))
                    dst_episode_seq_anim = os.path.normpath(os.path.join(delivery_dst, episode_seq_anim.split('Z:\Projects\\')[-1]))
                    episode_seq_anim_maya = os.path.normpath(os.path.join(episode_seq_anim, 'workspace.mel'))
                    if not os.path.exists(dst_episode_seq_anim):
                        os.makedirs(dst_episode_seq_anim)
                    shutil.copy2(episode_seq_anim_maya, dst_episode_seq_anim)

                    if os.listdir(episode_seq_lay) == []:
                        error_file_path = os.path.join(delivery_dst, 'missing_layout_publishes.txt')
                        with open(error_file_path, 'a') as f:
                            f.write(episode_seq_lay + '\n')                       
                    
                    else:
                        lay_file_basename = os.path.basename(latest_lay_file).split(".")
                        lay_file_newname =  str(lay_file_basename[0]) + "Anim.v001." + str(lay_file_basename[-1])
                        lay_file_new_path = os.path.normpath(os.path.join(dst_episode_seq_anim, lay_file_newname))
                        lay_file_old_dpath = os.path.normpath(os.path.join(dst_episode_seq_anim, os.path.basename(latest_lay_file)))
                        shutil.copy2(latest_lay_file, dst_episode_seq_anim)
                        #note: os.rename moves the file!  Don't even let it touch the original project folder!
                        print lay_file_old_dpath
                        print "new path ", lay_file_new_path
                        #patch for weird error happening in episode 3
                        if "sh121.v008.ma" not in lay_file_old_dpath:
                            os.rename(lay_file_old_dpath, lay_file_new_path)
                        else: 
                            continue



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--project', default='Worry Eaters')
    parser.add_argument('episode', help='e03_UnluckyBreak')
    parser.add_argument('-d', '--delivery', default='Z:/Projects/worry_eaters/deliverables/script_output/project')

    args = parser.parse_args()
    delivery_dst = os.path.normpath(args.delivery)
    if not os.path.exists(delivery_dst):
        os.makedirs(delivery_dst)
    sg_assets = sg.find('Asset', [['project.Project.name', 'is', args.project], ['episodes.Episode.code', 'is', args.episode]], ['code', 'sg_published_files'])
    if args.project == 'Worry Eaters':
        sg_assets_all = sg.find('Asset', [['project.Project.name', 'is', args.project], ['episodes.Episode.code', 'is', 'AllEpisode']], ['code', 'sg_published_files'])

    print 'start time', str(datetime.now())
    episode_path, episode_name, episode_prefix, episode_path_list = find_and_copy_episode_path(args.episode)
    find_and_copy_asset_path(delivery_dst, find_latest_asset_publish(sg_assets, delivery_dst))
    if len(sg_assets_all) > 0:
        find_and_copy_asset_path(delivery_dst, find_latest_asset_publish(sg_assets_all, delivery_dst))
    copy_audio_path(episode_path, episode_name, delivery_dst)
    copy_anim_layout_path(episode_path, episode_prefix, episode_path_list, delivery_dst)
    print 'end time', str(datetime.now())
    print 'All Done. YOU NEED TO MANUALLY COPY ANIMATICS. Thanks.'


if __name__ == '__main__':
    main()
