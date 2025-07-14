import streamlit as st
import re # For general string operations if needed, though mostly direct string methods suffice
import io # For handling file-like objects

st.set_page_config(layout="centered") # Optional: makes the app content centered

def rtrim(s: str) -> str:
    """Helper function to trim trailing spaces."""
    return s.rstrip(' ')

def is_blank(s: str) -> bool:
    """Helper function to check if a substring consists only of spaces."""
    return s.isspace()

def format_float_custom(value: float) -> str:
    """
    Helper function to format a floating-point number with high precision,
    then truncate to 6 characters, replicating the C++ behavior (fixed, precision 6, then substr(0,6)).
    """
    # Format to 6 decimal places
    formatted_str = f"{value:.6f}"
    # Then take the first 6 characters
    return formatted_str[:6]

def process_text_file(input_text: str, bar_list_set: set[int]) -> str:
    """
    Processes the input text content based on the C++ logic.
    Args:
        input_text: The entire content of the uploaded text file as a string.
        bar_list_set: A set of integers representing the bar list for matching.
    Returns:
        The processed text content as a single string.
    """
    output_lines = []
    lines = input_text.splitlines()

    found_dcir = False
    processing_data = False
    header_lines_remaining = 0

    for line in lines:
        if not found_dcir:
            if line.startswith("DCIR"):
                found_dcir = True
                header_lines_remaining = 2
                output_lines.append(line)
                continue
            else:
                output_lines.append(line)
                continue

        if header_lines_remaining > 0:
            output_lines.append(line)
            header_lines_remaining -= 1
            if header_lines_remaining == 0:
                processing_data = True
            continue

        if line.startswith("99999"):
            output_lines.append(line)
            # Append remaining lines after "99999" and break
            # In Python, we can just append the rest of the lines
            # after the current index, but given the loop structure,
            # this means we append the rest of `lines` and exit.
            current_line_index = lines.index(line) # Find current line index
            output_lines.extend(lines[current_line_index + 1:])
            break # Exit the loop after processing 99999 and subsequent lines

        if len(line) >= 42 and line[16] == 'T':
            bar1 = 0
            bar2 = 0
            try:
                # C++ substr(0, 6) for bar1
                bar1 = int(line[0:6].strip())
            except ValueError:
                pass # Skip invalid conversions

            try:
                # C++ substr(7, 5) for bar2
                bar2 = int(line[7:12].strip())
            except ValueError:
                pass # Skip invalid conversions

            bar_match = (bar1 in bar_list_set) or (bar2 in bar_list_set)

            # Python string slicing: [start:end] where end is exclusive
            # C++ substr(pos, len)
            # field18_23: C++ substr(17, 6) -> Python line[17:17+6] -> line[17:23]
            field18_23 = line[17:23]
            # field24_29: C++ substr(23, 6) -> Python line[23:23+6] -> line[23:29]
            field24_29 = line[23:29]
            # field30_35: C++ substr(29, 6) -> Python line[29:29+6] -> line[29:35]
            field30_35 = line[29:35]
            # field36_41: C++ substr(35, 6) -> Python line[35:35+6] -> line[35:41]
            field36_41 = line[35:41]

            if bar_match:
                modified_line = list(line) # Convert to list to modify characters

                if is_blank(field18_23):
                    try:
                        # C++ std::stod(rtrim(field24_29)) / 50.0;
                        value = float(rtrim(field24_29)) / 50.0
                        formatted = format_float_custom(value)
                        # C++ line.replace(17, 6, formatted.substr(0, 6));
                        # Python: replace characters at index 17 for 6 characters
                        for i in range(6):
                            if i < len(formatted): # Ensure we don't go out of bounds of formatted string
                                modified_line[17 + i] = formatted[i]
                            else:
                                modified_line[17 + i] = ' ' # Pad with spaces if formatted is shorter
                    except ValueError:
                        pass # Skip if conversion fails

                if is_blank(field30_35):
                    try:
                        # C++ std::stod(rtrim(field36_41)) / 50.0;
                        value = float(rtrim(field36_41)) / 50.0
                        formatted = format_float_custom(value)
                        # C++ line.replace(29, 6, formatted.substr(0, 6));
                        # Python: replace characters at index 29 for 6 characters
                        for i in range(6):
                            if i < len(formatted):
                                modified_line[29 + i] = formatted[i]
                            else:
                                modified_line[29 + i] = ' ' # Pad with spaces
                    except ValueError:
                        pass # Skip if conversion fails
                
                output_lines.append("".join(modified_line))
            else:
                output_lines.append(line)
        else:
            output_lines.append(line)
    
    return "\n".join(output_lines)

# --- Streamlit App Layout ---
st.title("Text File Processor")
st.markdown("Upload a text file, specify bar numbers, and process it based on the C++ logic.")

# 1. Bar List Input Control
st.sidebar.header("Configuration")
bar_list_input = st.sidebar.text_input(
    "Enter Bar Numbers (comma-separated)",
    value="100,200,300", # Example default value
    help="Enter integers separated by commas (e.g., 100, 200, 300, 400)"
)

bar_numbers = set()
if bar_list_input:
    # Clean input and convert to set of integers
    try:
        bar_numbers = {int(x.strip()) for x in bar_list_input.split(',') if x.strip()}
    except ValueError:
        st.sidebar.error("Invalid input for Bar Numbers. Please enter comma-separated integers.")

st.sidebar.write(f"Bar Numbers to check: {list(bar_numbers)}") # Display current bar list


# 2. File Uploader
uploaded_file = st.file_uploader("Upload your input text file (.txt)", type=["txt"])

processed_content = None

if uploaded_file is not None:
    st.write("File uploaded successfully!")
    file_contents = uploaded_file.getvalue().decode("utf-8")

    if st.button("Process File"):
        with st.spinner("Processing file..."):
            try:
                processed_content = process_text_file(file_contents, bar_numbers)
                st.success("File processed successfully!")
            except Exception as e:
                st.error(f"An error occurred during processing: {e}")
                st.exception(e) # Display full exception for debugging

# 3. Download Option
if processed_content:
    st.subheader("Processed Output")
    # You can also show a preview if the file is not too large
    # st.text_area("Preview", processed_content[:1000], height=300) 

    # Provide download button for the processed file
    st.download_button(
        label="Download Processed File",
        data=processed_content.encode("utf-8"), # Encode string to bytes for download
        file_name="processed_output.txt",
        mime="text/plain"
    )

st.info("Note: This app replicates the specific string manipulation and formatting logic from the provided C++ code. Ensure your input file format matches the expected structure.")
