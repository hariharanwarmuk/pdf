import fitz  # PyMuPDF

class TextBlock:
    def __init__(self, x0, y0, x1, y1, text, block_no):
        self.x0 = x0
        self.y0 = y0
        self.x1 = x1
        self.y1 = y1
        self.text = text
        self.block_no = block_no

    def __repr__(self):
        # Print a minimal but useful representation
        return f"TextBlock(block_no={self.block_no}, coords=({self.x0:.1f},{self.y0:.1f},{self.x1:.1f},{self.y1:.1f}), text={self.text.strip()!r})"

def extract_text_blocks(pdf_path, page_index=0):
    """
    Extract blocks from the given PDF page using PyMuPDF,
    and return them sorted top-to-bottom, then left-to-right.
    """
    doc = fitz.open(pdf_path)
    if page_index >= len(doc):
        raise ValueError(f"PDF has only {len(doc)} pages, cannot load page {page_index}")
    page = doc.load_page(page_index)
    
    raw_blocks = page.get_text("blocks")  # returns [x0, y0, x1, y1, text, block_no]
    blocks = []
    for b in raw_blocks:
        x0, y0, x1, y1, text, block_no = b
        blocks.append(TextBlock(x0, y0, x1, y1, text, block_no))
    
    # Sort in ascending y, then ascending x (typical reading order)
    blocks.sort(key=lambda blk: (blk.y0, blk.x0))
    return blocks

def group_blocks(blocks):
    """
    Produce 4 groups exactly as requested:
      Group 1: 'RESTRICTED'
      Group 2: 'Programme/Project Status Report' + lines physically close to it
      Group 3: 'Description' + lines physically close to it
      Group 4: 'Report Parameters' + lines physically close to it
      
    We'll do a simple approach:
      1) If block text includes 'RESTRICTED', that goes to Group 1 (alone).
      2) If block text includes 'Programme/Project Status Report', we label that as heading for Group 2.
         We also accept subsequent lines nearby in the y-direction until we encounter the next known heading ('Description').
      3) If block text includes 'Description', that's the heading for Group 3. We keep collecting blocks
         until we find 'Report Parameters' or run out.
      4) If block text includes 'Report Parameters', that's heading for Group 4. We also gather
         subsequent lines that appear close below it or contain known subheadings like
         'Milestones / Key Tasks...' and 'Risks, Issues...' in the text.
    
    The final returned structure is [group1, group2, group3, group4].
    Each group is a list of TextBlock.
    
    **Note**: If your real PDFs vary significantly, you may need a more robust approach.
    """
    # Prepare empty buckets
    group1 = []
    group2 = []
    group3 = []
    group4 = []

    # Simple flags / states
    in_group2 = False
    in_group3 = False
    in_group4 = False

    for blk in blocks:
        txt_clean = blk.text.strip().lower()
        
        # 1) If this block is "RESTRICTED", put it alone in group1
        #    (The example has only one "RESTRICTED" block, so let's assume that.)
        if "restricted" in txt_clean:
            group1.append(blk)
            continue  # do not assign it to any other group

        # 2) If this block is "Programme/Project Status Report" => start group2
        #    Also set a flag so subsequent lines also go to group2 until we see "Description"
        if "programme/project status report" in txt_clean:
            in_group2 = True
            in_group3 = False
            in_group4 = False
            group2.append(blk)
            continue
        
        # 3) If we encounter "Description" => start group3
        if "description" in txt_clean:
            in_group2 = False
            in_group3 = True
            in_group4 = False
            group3.append(blk)
            continue

        # 4) If we encounter "report parameters" => start group4
        if "report parameters" in txt_clean:
            in_group2 = False
            in_group3 = False
            in_group4 = True
            group4.append(blk)
            continue
        
        # If none of the above headings are triggered, then the block is a "follower"
        # that belongs to whichever heading group is currently active
        if in_group2:
            # Keep appending to group2
            group2.append(blk)
        elif in_group3:
            # Keep appending to group3
            group3.append(blk)
        elif in_group4:
            # Keep appending to group4
            group4.append(blk)
        else:
            # If we haven't hit a recognized heading, you might decide to ignore
            # or maybe default to group4. For the example, let's do nothing.
            pass
    
    return [group1, group2, group3, group4]

def main():
    pdf_path = "test.pdf"  # <--- put your PDF path here
    blocks = extract_text_blocks(pdf_path, page_index=0)

    # Now group them per the logic above
    g1, g2, g3, g4 = group_blocks(blocks)

    # Print the results
    print("\n--- Group 1 ---")
    for b in g1:
        print(b)
    print("\n--- Group 2 ---")
    for b in g2:
        print(b)
    print("\n--- Group 3 ---")
    for b in g3:
        print(b)
    print("\n--- Group 4 ---")
    for b in g4:
        print(b)


if __name__ == "__main__":
    main()
