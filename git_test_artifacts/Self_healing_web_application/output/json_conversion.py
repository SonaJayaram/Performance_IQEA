import pandas as pd
import json

def excel_to_nested_json(file_path):
    # Read Excel (no headers)
    df = pd.read_excel(file_path, header=None, dtype=str)

    # Take only 2nd and 3rd columns
    df = df.iloc[:, [1, 2]]
    df.columns = ["key", "value"]

    # Clean whitespace
    df["key"] = df["key"].astype(str).str.strip()
    df["value"] = df["value"].astype(str).str.strip()

    # Drop empty rows
    df = df[(df["key"] != "nan") & (df["value"] != "nan")].reset_index(drop=True)

    def parse_group(start_idx, current_group=None):
        """Recursive parser for nested group structures."""
        result = []
        current_obj = {}
        i = start_idx

        while i < len(df):
            key = df.loc[i, "key"]
            val = df.loc[i, "value"]

            if key.lower() == "group":
                # Found a new group
                group_name = val

                # If we’re entering a sub-group (nested inside current)
                if current_group is not None and group_name != current_group:
                    sub_items, next_i = parse_group(i + 1, group_name)
                    current_obj[group_name] = sub_items
                    i = next_i
                    continue

                # If it's the same group name again — push current object and start a new one
                elif current_group == group_name:
                    result.append(current_obj)
                    current_obj = {}
                    i += 1
                    continue

                # If it’s a new top-level group
                else:
                    sub_items, next_i = parse_group(i + 1, group_name)
                    result = sub_items
                    return {group_name: result}, next_i

            else:
                # Normal key-value pair
                current_obj[key] = val
                i += 1

                # Stop current object if next is a new group at same or parent level
                if i < len(df) and df.loc[i, "key"].lower() == "group":
                    next_group = df.loc[i, "value"]
                    if current_group == next_group or current_group is None:
                        continue
                    else:
                        break

        # Add last object if exists
        if current_obj:
            result.append(current_obj)

        return result, i

    # Parse top-level fields first (before first "group")
    top_level = {}
    i = 0
    while i < len(df):
        key = df.loc[i, "key"]
        val = df.loc[i, "value"]

        if key.lower() == "group":
            group_name = val
            sub_items, next_i = parse_group(i + 1, group_name)
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

    # Save to file
    with open("output.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    print(json.dumps(result, indent=2))
