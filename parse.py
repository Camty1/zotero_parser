import os
import shutil
from PyPDF2 import PdfReader

def load_dict(dict_file, note_dir):
    if os.path.exists(dict_file):
        file = open(dict_file, 'r')
    else:
        return generate_dict(dict_file, note_dir)
    
    lines = file.readlines()
    file.close()
    paper_dict = {}
    for line in lines:
        key_value_list = line.split(': ')

        # There is an error with the file since this should never happen
        if len(key_value_list) > 2:
            print("houston, we have a problem")
            return -1
        
        paper_dict[key_value_list[0]] = key_value_list[1].strip()
    return paper_dict

def generate_dict(dict_file, note_dir):
    notes = os.listdir(note_dir)
    paper_dict = {}
    
    for note in notes:
        # Open note file and get important data
        note_file_path = os.path.join(note_dir, note)
        note_file = open(note_file_path, 'r')
        title_line = note_file.readline()
        pdf_line = note_file.readline()
        note_file.close()
        
        # Get name of pdf file from dictionary
        pdf_start = pdf_line.find('[') + 2
        pdf_end = pdf_line.find(']')
        pdf_name = pdf_line[pdf_start:pdf_end]
        split_note = os.path.splitext(note)
        
        # Handle et al. since that messes up splitting by period
        if len(split_note) == 2:
            paper_dict[split_note[0]] = pdf_name
        else:
            paper_dict["".join([split_note[0], ".", split_note[1]])] = pdf_name
    
    return paper_dict

def save_dict(paper_dict, dict_file):
    file = open(dict_file, 'w')
    keys_list = list(paper_dict.keys())
    
    for key in keys_list:
        file.write("".join([key, ": ", paper_dict[key], "\n"]))

    file.close()

def has_PDF(folder):
    files = os.listdir(folder)

    for file in files:
        split_file = os.path.splitext(file)
        if split_file[1].lower() == ".pdf":
            return file

    return None 

def generate_key(pdf_file_name):
    split_file_name = pdf_file_name.split("-")

    return "".join([split_file_name[0], split_file_name[1].strip()])

def update_key(key):
    if key[-1].isdigit():
        return "".join([key, 'a'])
    new_letter = chr(ord(key[-1])+1)
    return "".join([key[:-1], new_letter])

def get_title_from_pdf(pdf_folder_path, pdf_file_name):

    with open(os.path.join(pdf_folder_path, pdf_file_name), 'rb') as f:
        pdf = PdfReader(f)
        info = pdf.metadata
        try:
            title = info['/Title']
        except:
            title = ""

        if len(title.strip()) == 0:
            print("Extracting title from pdf text, might have to fix")
            split_filename = pdf_file_name.split('-')
            index = 2 
            for i in range(len(split_filename)):
                if split_filename[i].strip().isnumeric():
                    index = i + 1
                    break
            just_title = "-".join(split_filename[index:]).strip()
            split_just_title = just_title.split('.')

            text = pdf.pages[0].extract_text()
            print(text)
            for line in text.split('\n'):
                if split_just_title[0].lower() in line.lower():
                    title = line
                    break

    return title

def create_note_file(pdf_folder_path, note_dir, key, pdf_file_name):
    #info_file_path = os.path.join(pdf_folder_path, ".zotero-ft-info")
    #info_file = open(info_file_path, "r")
    #paper_title = info_file.readline()
    #info_file.close()
    
    #paper_title_split = paper_title.split(":")
    #paper_title = "".join([paper_title_split[0], ": ", paper_title_split[1].strip()])
    
    paper_title = get_title_from_pdf(pdf_folder_path, pdf_file_name)

    note_file_name = "".join([key, ".md"])
    print(paper_title)
    print(note_file_name)
    note_file_path = os.path.join(note_dir, note_file_name)
    
    assert not os.path.isfile(note_file_path), "".join([key, " already exists, will not overwrite"])
    
    note_file = open(note_file_path, "w")
    note_file.write('Title: ' + paper_title)
    note_file.write("\nPDF: [[")
    note_file.write(pdf_file_name)
    note_file.write("]]\nTags: #unread #todo\n\n")
    note_file.close()

if __name__ == "__main__":
    # TODO: Add command line parsing
    zotero_directory = ''
    current_path = os.path.dirname(__file__)
    pdf_dir = os.path.join(current_path, '../PDFs')
    note_dir = os.path.join(current_path, '../Notes')
    dict_name = ".paper_dict"
    
    paper_dict = load_dict(dict_name, note_dir)

    cache_folders = os.listdir(zotero_directory)

    for folder in cache_folders:
        folder_path = os.path.join(zotero_directory, folder)
        pdf_file_name = has_PDF(folder_path)
        print(folder, ":", pdf_file_name)

        if pdf_file_name != None:
            key = generate_key(pdf_file_name)
            has_match = False

            while key in paper_dict and not has_match:
                has_match = paper_dict[key] == pdf_file_name

                if not has_match:
                    key = update_key(key)

            if not has_match:
                create_note_file(folder_path, note_dir, key, pdf_file_name)
                pdf_file_path = os.path.join(folder_path, pdf_file_name)
                shutil.copy(pdf_file_path, pdf_dir)
                paper_dict[key] = pdf_file_name

    save_dict(paper_dict, dict_name)
