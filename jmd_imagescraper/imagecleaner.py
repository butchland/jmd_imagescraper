# AUTOGENERATED! DO NOT EDIT! File to edit: 01_imagecleaner.ipynb (unless otherwise specified).

__all__ = ['display_image_cleaner']

# Cell
from pathlib import Path
from PIL import Image as PImage
from PIL import ImageDraw as PImageDraw
import ipywidgets as widgets
from IPython.display import display
from io import BytesIO

# Internal Cell

##########################################################################################
# globals & event handlers
##########################################################################################
ICLN_BATCH_SZ = 8

# this may look nauseating and but creating new widgets is literally about 10x slower than
# updating existing ones so the ui gets created once and updated forever more
icln_base_path = None
icln_folder = None
icln_batches = None
icln_pager = None
icln_grid = None
icln_empty_folder = None

def delete_on_click(btn):
  fn, img, batch, idx = btn.tag
  img.value = icln_deleted_img() # display red 'deleted' cross
  icln_batches[batch][idx] = ""  # so we know it's deleted as we page back & forth
  btn.disabled = True
  try:    Path(fn).unlink()      # dbl-clicks result in us trying to delete twice
  except: pass

def paging_on_click(btn):
  folder, batch = btn.tag
  icln_render_batch(folder, batch)

def reload_on_click(btn):
  icln_render_batch(icln_folder, 0, force_reload=True)

def folder_on_change(change):
  if(change["type"] == "change" and change["name"] == "value"):
    icln_render_batch(change["new"], 0)

##########################################################################################
# UI creation
##########################################################################################
def icln_deleted_img():
  # creates the red "deleted" placeholder cross and caches it
  DELETED_IMG = "deleted_img"

  if(DELETED_IMG not in icln_deleted_img.__dict__):
    img = PImage.new("RGB",(150,150), color="white")

    draw = PImageDraw.Draw(img)
    draw.line((5, 5, 140, 140), fill="red", width=10)
    draw.line((5, 140, 140, 5), fill="red", width=10)

    bio = BytesIO()
    img.save(bio, 'JPEG')
    icln_deleted_img.__dict__[DELETED_IMG] = bio.getvalue()

  return icln_deleted_img.__dict__[DELETED_IMG]

def icln_create_widgets(batch_size):
  # create the UI widgets
  global icln_pager
  global icln_grid
  global icln_empty_folder

  # image/delete button pairs
  display_items = []
  for i in range(batch_size):
    img = widgets.Image()
    img.layout.width="150px"
    btn = widgets.Button(description="Delete")
    btn.on_click(delete_on_click)
    box = widgets.VBox(children=[img,btn])
    box.layout.margin = "5px"
    display_items.append(box)

  # paging
  btnFirst = widgets.Button(description="|<<")
  btnPrev = widgets.Button(description="<<")
  lblPage = widgets.Label(value="Page NNN of KKK")
  lblPage.layout = widgets.Layout(display="flex", justify_content="center", width="100px")
  btnNext = widgets.Button(description=">>")
  btnLast = widgets.Button(description=">>|")

  pgbtns = [btnFirst, btnPrev, btnNext, btnLast]
  for btn in pgbtns: btn.on_click(paging_on_click)
  for btn in pgbtns: btn.layout.width = "60px"

  # folder drop down
  folders = [f.stem for f in icln_base_path.glob("*") if (f.is_dir() and f.stem[0] != ".")]
  folders.sort()
  rootfiles = [f for f in icln_base_path.glob("*.jpg") if f.is_file()]
  if(len(rootfiles) > 0): folders = ["/"] + folders
  ddlFolder = widgets.Dropdown(options=folders, description="Folder: ")
  ddlFolder.observe(folder_on_change)

  # reload button
  btnReload = widgets.Button(description="↻")
  btnReload.layout = widgets.Layout(width="40px", margin="0px 0px 0px 10px")
  btnReload.on_click(reload_on_click)

  # plug it all in and display
  icln_pager = widgets.HBox(children=[btnFirst, btnPrev, lblPage, btnNext, btnLast,
                                      ddlFolder, btnReload])
  icln_grid = widgets.GridBox(display_items,
                              layout=widgets.Layout(grid_template_columns="repeat(4, 25%)",
                                                    margin="15px"))
  icln_empty_folder = widgets.HTML(value="<h2>No images left to display in this folder.</h2>")
  icln_empty_folder.layout.visibility = "hidden"

  display(icln_pager)
  display(icln_empty_folder)
  display(icln_grid)

##########################################################################################
# UI rendering
##########################################################################################
def icln_render_batch(folder, batch, force_reload=False):
  global icln_folder
  global icln_batches
  global icln_pager
  global icln_grid

  if(folder == "/"): folder = ""
  path = icln_base_path/folder

  if((icln_folder != folder) or (force_reload)):
    # get the files, split into batches
    files = list(path.glob("*.jpg"))
    icln_batches = [files[i:i + ICLN_BATCH_SZ] for i in range(0, len(files), ICLN_BATCH_SZ)]
    icln_folder = folder

    if(len(files) == 0):
      # fail gracefully if they've deleted every image in this folder
      icln_empty_folder.layout.visibility = "visible"
      # icln_grid.layout.visibility = "hidden" <-- doesn't work :-@
      for child in icln_grid.children: child.layout.visibility = "hidden"
      btnFirst, btnPrev, lblPage, btnNext, btnLast,_,_ = icln_pager.children
      lblPage.value = "Page 0 of 0"
      for btn in [btnFirst, btnPrev, btnNext, btnLast]: btn.disabled = True
      return
    else:
      icln_empty_folder.layout.visibility = "hidden"
      icln_grid.layout.visibility = "visible"

  # display the images
  for i, fp in enumerate(icln_batches[batch]):
    icln_grid.children[i].layout.visibility = "visible"
    img = icln_grid.children[i].children[0]
    btn = icln_grid.children[i].children[1]

    if(fp == ""):
      img.value = icln_deleted_img()
      btn.disabled = True
    else:
      img.value = open(fp, "rb").read()
      btn.tag = (fp, img, batch, i)
      btn.disabled = False

  if(len(icln_batches[batch]) < ICLN_BATCH_SZ):
    # partial batch on the last page, hide the rest of the grid
    for i in range(len(icln_batches[batch]), ICLN_BATCH_SZ):
      icln_grid.children[i].layout.visibility = "hidden"

  # update the paging controls
  btnFirst, btnPrev, lblPage, btnNext, btnLast,_,_ = icln_pager.children
  btnFirst.tag = (folder, 0)
  btnPrev.tag = (folder, max(0, batch-1))
  btnNext.tag = (folder, min(len(icln_batches)-1, batch+1))
  btnLast.tag = (folder, len(icln_batches)-1)
  lblPage.value = "Page {} of {}".format(batch+1, len(icln_batches))
  for btn in [btnFirst, btnPrev, btnNext, btnLast]: btn.disabled = btn.tag[1] == batch

# Cell
def display_image_cleaner(path):
    '''Display the image cleaner widget for the given folder'''
    global icln_base_path; icln_base_path = Path(path)

    icln_create_widgets(ICLN_BATCH_SZ)
    _,_,_,_,_,ddlFolder,_ = icln_pager.children
    icln_render_batch(ddlFolder.value, 0)