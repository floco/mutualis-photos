""" Export all photos to specified directory using album names as folders
    If file has been edited, also export the edited version, 
    otherwise, export the original version 
    This will result in duplicate photos if photo is in more than album """

import os.path
import pathlib
import sys
import re

import click
from pathvalidate import is_valid_filepath, sanitize_filepath

import osxphotos


@click.command()
@click.argument("export_path", type=click.Path(exists=True))
@click.option(
    "--default-album",
    help="Default folder for photos with no album. Defaults to 'unfiled'",
    default="unfiled",
)
@click.option(
    "--library-path",
    help="Path to Photos library, default to last used library",
    default=None,
)
@click.option(
    "--include-filter",
    help="Regex matching the album names to export ",
    default=".*",
)
def export(export_path, default_album, library_path, include_filter):
    export_path = os.path.expanduser(export_path)
    library_path = os.path.expanduser(library_path) if library_path else None

    if library_path is not None:
        photosdb = osxphotos.PhotosDB(library_path)
    else:
        photosdb = osxphotos.PhotosDB()

    # get list of albums
    albums = sorted(photosdb.albums, reverse=True)

    # prepare filter
    include_filter_regex = re.compile(include_filter)

    # export each albums
    for album in albums:
        if include_filter_regex.match(album):
            photos = photosdb.photos(albums=[album], images=True, movies=True)
            click.echo(f"********* Exporting ALBUM {album} ({len(photos)})... ***********")

            # make sure no invalid characters in destination path (could be in album name)
            album_name = sanitize_filepath(album, platform="auto")
            album_name = album_name.replace(" ", "_")

            # create destination folder, if necessary, based on album name
            dest_dir = os.path.join(export_path, album_name)

            # verify path is a valid path
            if not is_valid_filepath(dest_dir, platform="auto"):
                sys.exit(f"Invalid filepath {dest_dir}")

            # create destination dir if needed
            if not os.path.isdir(dest_dir):
                os.makedirs(dest_dir)

            # export each photos in album
            for p in photos:
                if not p.ismissing:
                        # export the photo
                        #original_path, original_ext = os.path.splitext(p.original_filename)
                        # click.echo(f"Exporting {p.original_filename} ...")
                        if p.hasadjustments and p.path_edited:
                            # export edited version
                            edited_name = pathlib.Path(p.path_edited).name
                            #edited_path, edited_ext = os.path.splitext(edited_name)
                            #edited_filename = original_path + "_edited" + edited_ext
                            edited_filename = edited_name
                            if os.path.exists(os.path.join(dest_dir,edited_filename)):
                                click.echo(f"Ignored {edited_filename} - already exist")  
                            elif not os.path.exists(p.path_edited):
                                click.echo(f"Can't find {p.path_edited} in library") 
                            else: 
                                exported = p.export(dest_dir, edited=True)
                                #exported = p.export(dest_dir, edited_filename, edited=True)
                                #click.echo(f"Exported {edited_filename}")
                        # export unedited version
                        #new_path, new_ext = os.path.splitext(p.filename)
                        #filename = original_path + new_ext
                        filename = p.filename                      
                        if os.path.exists(os.path.join(dest_dir,filename)):
                            click.echo(f"Ignored {filename} - already exist")
                        elif not os.path.exists(p.path):
                            click.echo(f"Can't find {p.path} in library")   
                        else:    
                            exported = p.export(dest_dir) 
                            #exported = p.export(dest_dir, filename)
                            #click.echo(f"Exported {filename}")
                else:
                    click.echo(f"Skipping missing photo: {p.original_filename}")

            # TODO: handle photos that are not in an album
            # albums = p.albums
            # if not albums:
            #     albums = [default_album]


if __name__ == "__main__":
    export()  # pylint: disable=no-value-for-parameter