import pandas as pd
import json

def excel_to_nested_json(file_path):
    # Read Excel (no headers)
    df = pd.read_excel(file_path, header=None, dtype=str)

    # Consider only 2nd and 3rd columns
    df = df.iloc[:, [1, 2]]
    df.columns = ["key", "value"]

    # Clean whitespace
    df["key"] = df["key"].astype(str).str.strip()
    df["value"] = df["value"].astype(str).str.strip()

    # Drop empty rows
    df = df[(df["key"] != "nan") & (df["value"] != "nan")].reset_index(drop=True)

    def parse_group(start_idx, current_group=None, parent_group=None):
        """Recursively parse rows starting from start_idx into structured JSON."""
        result = []
        current_obj = {}
        i = start_idx

        while i < len(df):
            key = df.loc[i, "key"]
            val = df.loc[i, "value"]

            if key.lower() == "group":
                group_name = val

                # CASE 1: New child group (contains parent group name)
                if parent_group and group_name.startswith(parent_group + "_"):
                    sub_items, next_i = parse_group(i + 1, group_name, parent_group=group_name)
                    current_obj[group_name] = sub_items
                    i = next_i
                    continue

                # CASE 2: Another object in the same group
                elif current_group == group_name:
                    result.append(current_obj)
                    current_obj = {}
                    i += 1
                    continue

                # CASE 3: New nested child under current group
                elif current_group and group_name.startswith(current_group + "_"):
                    sub_items, next_i = parse_group(i + 1, group_name, parent_group=current_group)
                    current_obj[group_name] = sub_items
                    i = next_i
                    continue

                # CASE 4: New top-level group (not related to current)
                elif not current_group:
                    sub_items, next_i = parse_group(i + 1, group_name, parent_group=group_name)
                    return {group_name: sub_items}, next_i

                # CASE 5: Unrelated group, stop and return up
                else:
                    result.append(current_obj)
                    return result, i

            else:
                # Normal parameter
                current_obj[key] = val
                i += 1

                # Stop if next row begins a new unrelated group
                if i < len(df) and df.loc[i, "key"].lower() == "group":
                    next_group = df.loc[i, "value"]
                    if current_group and not next_group.startswith(current_group):
                        break

        # Add last object if not empty
        if current_obj:
            result.append(current_obj)

        return result, i

    # --- Parse all rows ---
    top_level = {}
    i = 0
    while i < len(df):
        key = df.loc[i, "key"]
        val = df.loc[i, "value"]

        if key.lower() == "group":
            group_name = val
            sub_items, next_i = parse_group(i + 1, group_name, parent_group=group_name)
            top_level[group_name] = sub_items
            i = next_i
        else:
            top_level[key] = val
            i += 1

    return top_level


# Example usage
if __name__ == "__main__":
    file_path = r"C:\Users\sathanantham.aru\Downloads\API_POC_Response.xlsx"  # your Excel file path
    result = excel_to_nested_json(file_path)

    with open("output.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    print(json.dumps(result, indent=2))
