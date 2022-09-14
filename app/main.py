from configparser import ConfigParser
import os
import mutagen
from ytmusicapi import YTMusic
import music_tag


def download_songs(songs, path):
    if int(ini["behavior.unavailable_songs"]["abandon"]):
        unavailable_song_ids = open(ini["behavior.unavailable_songs"]["path"], 'r').read().splitlines()

        def song_available(song):
            if song['id'] in unavailable_song_ids:
                if int(ini['logging']['enabled']):
                    log.info(f"Skipping song with ID {song['id']} because it's listed as unavailable.")
                return False
            return True

        songs = list(filter(song_available, songs))

    for song in songs:
        print(f"Downloading {song['artist']} - {song['title']}")
        os.system(
            "yt-dlp -f m4a --no-post-overwrites --embed-thumbnail -o \"" + path + "%(id)s.%(ext)s\" -- " +
            song["id"])
        print("Setting tags...")
        set_tags(path, song["id"], song["title"], song["artist"], song["album"])
        print()


def get_songs_from_playlist(pl):
    return [
        dict(id=song['videoId'], title=song['title'], artist=song['artists'][0]['name'],
             album=(song['album']['name'] if song['album'] else ''))
        for song in pl['tracks'][:limit] if pl['tracks'] and song['videoId']]


def queue_playlists_by_ids(playlist_ids):
    for playlist_id in playlist_ids:
        try:
            pl = y.get_playlist(playlist_id)
        except Exception:
            if int(ini['logging']['enabled']):
                log.error(f"Was not able to retrieve playlist with ID: {playlist_id}")
            return
        queue[pl["title"]] = get_songs_from_playlist(pl)


# The playlist name is going to be used as a directory name, so only use names allowed by filesystem
def sanitise_folder_name(folder_name):
    folder_name = folder_name.strip().replace("/", "⧸")
    if (folder_name.upper().startswith(("CON", "PRN", "AUX", "NUL")) and (len(folder_name) == 3 or folder_name[3] == '.')) or \
            (folder_name.upper().startswith(("COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
                                             "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9")) and
             (len(folder_name) == 4 or folder_name[4] == '.')):
        folder_name = '_' + folder_name
    return "".join([c if c not in "[\\\\/:*?\"<>|]" else " " for c in folder_name]).strip()


def set_tags(directory, file_id, title_tag, artist_tag, album_tag):
    if os.path.isfile(directory + file_id + '.m4a'):
        try:
            f = music_tag.load_file(directory + file_id + '.m4a')
            f['title'] = title_tag
            f['artist'] = artist_tag
            f['album'] = album_tag
            f.save()
        except (FileNotFoundError, mutagen.MutagenError):
            print("Error setting tags")
            if int(ini['logging']['enabled']):
                log.error(f"Couldn't load {directory + file_id} to set tags!")
            if int(ini["behavior.unavailable_songs"]["abandon"]):
                open(ini["behavior.unavailable_songs"]["path"], 'a').write(file_id + '\n')
            return


ini = ConfigParser()
ini.read("settings.ini")
limit = int(ini['behavior']['limit']) or 100000
y = YTMusic(ini['paths']['headers_file'])
queue = {'.': []}

if int(ini['logging']['enabled']):
    import logging as log

    log.basicConfig(filename=ini['logging']['path'], format='%(asctime)s %(levelname)-8s %(message)s', level=log.INFO,
                    datefmt='%y-%m-%d %H:%M:%S')


def main():
    cores = int(ini["multiprocessing"]["cores"]) if int(ini["multiprocessing"]["enabled"]) else 1
    if cores > 1:
        from multiprocessing import Process
        import numpy as np

    save_directory = ini['paths']['save_directory'] or "Music"
    print(f'Using directory "{save_directory}" for downloads')

    # QUEUEING STARTS HERE

    if int(ini["behavior.sync"]["liked_songs"]):
        # Add liked songs to download queue
        print("Queueing liked songs...")
        queue[sanitise_folder_name(ini['naming']['liked_songs_folder_name']) or "Your Likes"] = get_songs_from_playlist(
            y.get_liked_songs(limit))

    if int(ini["behavior.sync"]["library_playlists"]):
        # Add saved playlists from library to download queue
        print("Queueing library playlists...")
        library_playlist_ids = [pl['playlistId'] for pl in y.get_library_playlists()][1:]
        if cores > 1:
            procs = []
            library_playlist_ids_split = np.array_split(library_playlist_ids, cores)
            for library_playlist_ids in library_playlist_ids_split:
                proc = Process(target=queue_playlists_by_ids, args=(library_playlist_ids,))
                procs.append(proc)
                proc.start()
            for proc in procs:
                proc.join()
        else:
            queue_playlists_by_ids(library_playlist_ids)

    if int(ini["behavior.sync"]["subscriptions"]):
        # Add all songs of subscribed artist to download queue
        def queue_sub_discographies(subscriptions):
            for subscription in subscriptions:
                try:
                    artist_id, artist_name = subscription['browseId'], subscription['artist']
                    print(artist_name)
                    artist = y.get_artist(artist_id)

                    # Songs
                    artist_songs_browse_id = artist['songs']['browseId']
                    if artist_songs_browse_id:
                        queue['.'].extend(
                            [dict(id=song['videoId'], title=song['title'], artist=artist_name,
                                  album=(song['album']['name'] if song['album'] else ''))
                             for song in
                             y.get_playlist(artist_songs_browse_id)['tracks'] if song['videoId']])

                    # Singles
                    if 'singles' in artist:
                        for single in artist['singles']['results']:
                            single_detail = y.get_album(single["browseId"])['tracks'][0]
                            if single_detail['title'] and single_detail['videoId']:
                                queue['.'].append(
                                    dict(id=single_detail['videoId'], title=single_detail['title'], artist=artist_name,
                                         album=''))

                    # Videos
                    if 'videos' in artist:
                        artist_videos_browse_id = artist['songs']['browseId']
                        if artist_videos_browse_id:
                            queue['.'].extend(
                                [dict(id=song['videoId'], title=song['title'], artist=artist_name, album='') for song in
                                 y.get_playlist(artist_videos_browse_id)['tracks'] if song['videoId']])
                except Exception:
                    continue

        print("Queueing subscriptions...")
        subs = y.get_library_subscriptions(limit, "a_to_z")
        if cores > 1:
            procs = []
            subs_split = np.array_split(subs, cores)
            for subs in subs_split:
                proc = Process(target=queue_sub_discographies, args=(subs,))
                procs.append(proc)
                proc.start()
            for proc in procs:
                proc.join()
        else:
            queue_sub_discographies(subs)

    if ini['ids']['playlist_ids'].strip():
        # Add custom user-added playlist ID's to download queue
        print("Queueing custom playlists...")
        playlist_ids = [s.strip() for s in ini['ids']['playlist_ids'].split(",") if s]
        queue_playlists_by_ids(playlist_ids)

    for folder in list(queue):
        if folder != (newFolder := sanitise_folder_name(folder)):
            print(f'Renaming playlist "{folder}" to "{newFolder}" for offline use.')
            queue[newFolder] = queue.pop(folder)

    if int(ini["behavior.sync"]["playlist_deletions"]):
        # Synchronzse playlist deletions
        offline_dirs = set(name for name in os.listdir(".") if os.path.isdir(name))
        online_dirs = set(queue.keys())
        dirs_to_delete = offline_dirs - online_dirs
        if dirs_to_delete:
            from shutil import rmtree
            for dir_to_delete in dirs_to_delete:
                rmtree(dir_to_delete)

    # Start downloading what's missing
    print()
    if not save_directory.endswith("/"):
        save_directory += '/'
    for folder, songs in queue.items():
        if songs:  # if folder would contain any songs
            online_ids_sorted = list(dict.fromkeys([song["id"] for song in songs]))  # also removes duplicates
            folder += '/'
            path = save_directory + folder
            if os.path.exists(path):  # does folder already exist?
                # Lets check if it already has all the files
                online_ids = set(online_ids_sorted)
                offline_ids = {os.path.splitext(filename)[0] for filename in os.listdir(path) if
                               os.path.isfile(path + filename) and os.path.splitext(filename)[1] == "m4a"}
                if online_ids != offline_ids:
                    ids_to_delete = offline_ids - online_ids
                    if int(ini["behavior.sync"]["song_deletions"]):
                        for file_id in ids_to_delete:
                            print(f"Removing {path + file_id}.m4a")
                            try:
                                os.remove(path + file_id + ".m4a")
                            except FileNotFoundError:
                                if int(ini['logging']['enabled']):
                                    log.error(f"Couldn't delete {path + file_id}.m4a")
                                continue
                            except NotImplementedError:
                                os.remove(os.path.join(path, file_id + ".m4a"))
                    ids_to_download = online_ids - offline_ids
                    songs = [song for song in songs if song["id"] in ids_to_download]
                else:
                    continue
            else:
                os.makedirs(path)

            if cores > 1:
                procs = []
                songs_split = np.array_split(songs, cores)
                for songs_s in songs_split:
                    proc = Process(target=download_songs, args=(songs_s, path))
                    procs.append(proc)
                    proc.start()
                for proc in procs:
                    proc.join()
            else:
                download_songs(songs, path)

            # Order songs by adding track numbers
            print("Adding tracknumbers...")
            if folder != "./":
                for i in range(len(online_ids_sorted)):
                    print(f"Adding tracknumber to {path + online_ids_sorted[i]}.m4a")
                    if os.path.isfile(path + online_ids_sorted[i] + '.m4a'):
                        try:
                            f = music_tag.load_file(path + online_ids_sorted[i] + '.m4a')
                        except Exception:
                            if int(ini['logging']['enabled']):
                                log.error(f"Couldn't load {path + online_ids_sorted[i]}.m4a to add track number!")
                            continue
                        f['tracknumber'] = i + 1
                        f.save()

            print("Cleaning up...")
            filenames = next(os.walk(path))[2]
            for file_name in filenames:
                if not file_name.endswith(".m4a"):
                    os.remove(os.path.join(path, file_name))

    print("Done.")


if __name__ == "__main__":
    main()