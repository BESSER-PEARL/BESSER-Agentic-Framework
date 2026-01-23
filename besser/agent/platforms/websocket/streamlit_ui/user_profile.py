import streamlit as st
import json
import os
from besser.agent.platforms.websocket.streamlit_ui.user_db import UserDB


json_schema_path = os.path.join(os.path.dirname(__file__), "json_schema.json")
# Load the JSON schema
json_schema = {}

with open(json_schema_path, "r") as file:
    json_schema = json.load(file)


# Function to render forms dynamically
def render_form(schema, data_key=None):
    if "type" not in schema:
        return st.error(data_key)
    elif "type" in schema and schema["type"] == "object":
        for key, value in schema["properties"].items():
            if "$ref" in value:
                ref_name = value["$ref"].split("/")[-1]
                if ref_name == "Range":
                    name = f"{data_key}_{key}" if data_key else key
                    st.slider(f"{key}", min_value=0, max_value=100, value=st.session_state.get(name, -1), key=name)
                else:
                    if "enum" in json_schema["definitions"][ref_name]:
                        options = ["Select an option"] + json_schema["definitions"][ref_name]["enum"]
                        current = st.session_state.get(f"{data_key}_{key}", "Select an option")
                        index = options.index(current) if current in options else 0
                        st.selectbox(
                            key,
                            options,
                            index=index,
                            key=f"{data_key}_{key}"
                        )
                    else:
                        if ref_name not in st.session_state.visited_objects:
                            st.session_state.visited_objects.append(ref_name)
                            st.markdown(f"##### {key.capitalize()}")
                            name = f"{data_key}_{key}" if data_key else key
                            render_form(json_schema["definitions"][ref_name]["allOf"][0], name)
            elif value["type"] == "string":
                st.text_input(
                    f"{key.capitalize()}:",
                    value=st.session_state.get(f"{data_key}_{key}", ""),
                    key=f"{data_key}_{key}"
                )
            elif value["type"] == "integer":
                min_val = value.get("minimum", -1)
                max_val = value.get("maximum", 100)
                st.number_input(
                    f"{key.capitalize()}:",
                    min_value=min_val,
                    max_value=max_val,
                    value=st.session_state.get(f"{data_key}_{key}", min_val),
                    key=f"{data_key}_{key}"
                )
            elif value["type"] == "array":
                st.markdown(f"#### {key.capitalize()}")
                items = value.get("items", {})
                if "$ref" in items:
                    ref_name = items["$ref"].split("/")[-1]
                    if ref_name not in st.session_state.visited_objects:
                        st.markdown(f"Array of {ref_name}")
                        name = f"{data_key}_{key}" if data_key else key
                        if name not in st.session_state.arrays:
                            st.session_state.arrays[name] = []
                        for idx, item in enumerate(st.session_state.arrays.get(name)):
                            st.text(f"{ref_name} {idx + 1}: {item}")
                            if st.button(
                                f"Remove {ref_name} {idx + 1}", key=f"{ref_name}_{idx}"
                            ):
                                st.session_state.arrays[name].pop(idx)
                                st.rerun()
                        render_form(json_schema["definitions"][ref_name]["allOf"][0], name)
                        if st.button(f"Add {ref_name}", key=name):
                            new_object = {}
                            for item in json_schema["definitions"][ref_name]["allOf"][0]["properties"]:
                                if st.session_state.get(name+"_"+item) not in ["", "Select an option", -1]:
                                    new_object[item] = st.session_state.get(name+"_"+item)
                            st.markdown(new_object)
                            st.session_state.arrays[name].append(new_object)
                            st.rerun()
                else:
                    st.text_area(f"{key.capitalize()} (Array Items):", key=f"{data_key}_{key}")
    elif schema["type"] == "array":
        st.markdown(f"#### {data_key.capitalize()}")
        items = schema.get("items", {})
        if "$ref" in items:
            ref_name = items["$ref"].split("/")[-1]
            if ref_name == "Range":
                name = data_key
                st.slider("Select a value", min_value=0, max_value=100, value=st.session_state.get(name, -1), key=name)
            else:
                if ref_name not in st.session_state.visited_objects:
                    st.markdown(f"Array of {ref_name}")
                    name = data_key
                    if name not in st.session_state.arrays:
                        st.session_state.arrays[name] = []
                    for idx, item in enumerate(st.session_state.arrays.get(name)):
                        st.text(f"{ref_name} {idx + 1}: {item}")
                        if st.button(
                            f"Remove {ref_name} {idx + 1}", key=f"{ref_name}_{idx}"
                        ):
                            st.session_state.arrays[name].pop(idx)
                            st.rerun()
                    render_form(json_schema["definitions"][ref_name]["allOf"][0], name)
                    if st.button(f"Add {ref_name}"):
                        new_object = {}
                        for item in json_schema["definitions"][ref_name]["allOf"][0]["properties"]:
                            if st.session_state.get(name+"_"+item) not in ["", "Select an option", -1]:
                                new_object[item] = st.session_state.get(name+"_"+item)
                        st.markdown(new_object)
                        st.session_state.arrays[name].append(new_object)
                        st.rerun()
    else:
        st.error(f"Unsupported type: {schema['type']}")


# Function to extract user input based on schema
def extract_user_data(schema, data_key=None):
    user_data = {}
    if "type" not in schema:
        return user_data
    elif "type" in schema and schema["type"] == "object":
        for key, value in schema["properties"].items():

            base_key = data_key.rsplit('_', 1)[0] if data_key and '_' in data_key else data_key
            unique_key = f"{base_key}_{key}" if base_key else key
            if "$ref" in value:
                if "Range" in value["$ref"]:
                    user_data[key] = st.session_state.get(unique_key, None)
                else:
                    ref_name = value["$ref"].split("/")[-1]
                    if "allOf" in json_schema["definitions"].get(ref_name, {}):
                        user_data[key] = extract_user_data(json_schema["definitions"][ref_name]["allOf"][0], unique_key)
                    elif "enum" in json_schema["definitions"].get(ref_name, {}):
                        user_data[key] = st.session_state.get(unique_key, None)
            elif value["type"] == "string":
                text_value = st.session_state.get(unique_key, None)
                user_data[key] = None if text_value == "" else text_value
            elif value["type"] == "integer":
                user_data[key] = st.session_state.get(unique_key, None)
            elif value["type"] == "array":
                user_data[key] = st.session_state.arrays.get(unique_key, [])
    elif schema["type"] == "array":
        user_data = st.session_state.arrays.get(data_key, [])
    return user_data


def user_profile():
    """Render the user profile editor and return True when the user finishes editing.

    This is the entrypoint other modules import. It mirrors the behavior of the
    standalone `main()` but returns a boolean indicating whether to go back to
    the previous page (True) or stay on the profile page (False).
    """
    # Ensure session state keys exist
    st.session_state.setdefault("visited_objects", [])
    if "arrays" not in st.session_state:
        st.session_state.arrays = {}

    # Load the top-level user schema early so prefill logic can reference it
    user_schema = json_schema["definitions"]["User"]["allOf"][0]

    # Try to load existing profile for the current user (DB first, then env, then local JSON)
    username = st.session_state.get("username", "Guest")
    stored_profile = None
    try:
        db = UserDB()
        stored_profile = db.get_profile(username)
    except Exception:
        stored_profile = None

    if stored_profile is None:
        env_raw = os.environ.get("STREAMLIT_USER_PROFILES_JSON")
        if env_raw:
            try:
                env_data = json.loads(env_raw)
                candidate = None
                if isinstance(env_data, list):
                    candidate = next((p for p in env_data if isinstance(p, dict) and p.get("name") == username), None)
                    if candidate is None and env_data:
                        candidate = env_data[0]
                elif isinstance(env_data, dict):
                    candidate = env_data.get(username) or (next(iter(env_data.values())) if env_data else None)

                if isinstance(candidate, dict):
                    if "user_profile" in candidate:
                        stored_profile = candidate["user_profile"]
                    elif "User" in candidate:
                        stored_profile = candidate["User"]
                    else:
                        stored_profile = candidate
            except Exception:
                stored_profile = None

    if stored_profile is None:
        profiles_path = os.path.join(os.path.dirname(__file__), "user_profiles.json")
        if os.path.exists(profiles_path):
            try:
                with open(profiles_path, "r") as pf:
                    profiles = json.load(pf)
                    stored_profile = profiles.get(username)
            except Exception:
                stored_profile = None

    # Helper to prefill session_state following the same keys render_form creates
    def _prefill_schema(schema, data_key, value):
        # schema: JSON schema fragment
        # data_key: prefix used when render_form created widget keys
        # value: the stored data corresponding to this schema (may be None)
        if schema is None:
            return
        if schema.get("type") == "object":
            for prop, prop_schema in schema.get("properties", {}).items():
                unique_key = f"{data_key}_{prop}" if data_key else prop
                if "$ref" in prop_schema:
                    ref_name = prop_schema["$ref"].split("/")[-1]
                    if ref_name == "Range":
                        # numeric slider
                        val = None
                        if isinstance(value, dict):
                            val = value.get(prop)
                        if unique_key not in st.session_state:
                            st.session_state[unique_key] = val
                    else:
                        # enum or nested object
                        if "enum" in json_schema["definitions"].get(ref_name, {}):
                            val = None
                            if isinstance(value, dict):
                                val = value.get(prop)
                            if unique_key not in st.session_state:
                                st.session_state[unique_key] = val
                        else:
                            nested_name = unique_key
                            nested_value = None
                            if isinstance(value, dict):
                                nested_value = value.get(prop)
                            _prefill_schema(json_schema["definitions"][ref_name]["allOf"][0], nested_name, nested_value)
                else:
                    t = prop_schema.get("type")
                    if t == "string":
                        val = None
                        if isinstance(value, dict):
                            val = value.get(prop)
                        # set empty string if None so text_input shows blank
                        if unique_key not in st.session_state:
                            st.session_state[unique_key] = "" if val is None else val
                    elif t == "integer":
                        val = None
                        if isinstance(value, dict):
                            val = value.get(prop)
                        if unique_key not in st.session_state:
                            st.session_state[unique_key] = val
                    elif t == "array":
                        name = unique_key
                        if isinstance(value, dict):
                            arr_val = value.get(prop, [])
                        else:
                            arr_val = []
                        # store arrays in the same session_state structure used by render_form
                        if name not in st.session_state.arrays:
                            st.session_state.arrays[name] = arr_val
        elif schema.get("type") == "array":
            # top-level array with data_key as name
            name = data_key
            if isinstance(value, list):
                if name not in st.session_state.arrays:
                    st.session_state.arrays[name] = value

    # Prefill session state if we have stored data. stored_profile may be wrapped in {"User":...}
    profile_to_use = None
    if stored_profile is not None:
        if isinstance(stored_profile, dict) and "User" in stored_profile:
            profile_to_use = stored_profile.get("User")
        else:
            profile_to_use = stored_profile

    if profile_to_use:
        # Iterate top-level user schema and prefill accordingly (match render_form calls in main())
        for category, category_schema in user_schema["properties"].items():
            if "$ref" in category_schema:
                ref_name = category_schema["$ref"].split("/")[-1]
                # stored data keyed by category name
                cat_value = profile_to_use.get(category) if isinstance(profile_to_use, dict) else None
                _prefill_schema(json_schema["definitions"][ref_name]["allOf"][0], ref_name, cat_value)
            else:
                cat_value = profile_to_use.get(category) if isinstance(profile_to_use, dict) else None
                _prefill_schema(category_schema, category, cat_value)

    st.title("User Profile Editor")
    user_schema = json_schema["definitions"]["User"]["allOf"][0]
    for category, category_schema in user_schema["properties"].items():
        if "$ref" in category_schema:
            ref_name = category_schema["$ref"].split("/")[-1]
            with st.expander(ref_name, expanded=False):
                st.markdown(f"### Editing: {ref_name}")
                render_form(json_schema["definitions"][ref_name]["allOf"][0], ref_name)
        else:
            with st.expander(category, expanded=False):
                render_form(category_schema, category)

    # Save and navigation buttons
    cols = st.columns(2)
    save_clicked = cols[0].button("Save JSON")
    back_clicked = cols[1].button("Go Back")

    if save_clicked:
        user_data = {"User": extract_user_data(user_schema)}
        # Save a module-local copy
        with open(os.path.join(os.path.dirname(__file__), "user_model.json"), "w") as f:
            json.dump(user_data, f, indent=4)

        # Also save per-user profiles in `user_profiles.json` using username as key
        profiles_path = os.path.join(os.path.dirname(__file__), "user_profiles.json")
        try:
            if os.path.exists(profiles_path):
                with open(profiles_path, "r") as pf:
                    profiles = json.load(pf)
            else:
                profiles = {}
        except Exception:
            profiles = {}

        username = st.session_state.get("username", "Guest")
        # Store the raw user_data under the username key
        profiles[username] = user_data
        with open(profiles_path, "w") as pf:
            json.dump(profiles, pf, indent=4)

        # Also persist to the UserDB
        try:
            db = UserDB()
            ok = db.set_profile(username, user_data)
            if ok:
                st.success("JSON data has been saved to disk and DB")
            else:
                st.warning("Saved to disk, but failed to save profile to DB")
        except Exception:
            st.warning("Saved to disk, but could not connect to DB to save profile")

        st.json(user_data)
        return True

    if back_clicked:
        return True

    return False


def main():
    st.session_state.visited_objects = []
    if "arrays" not in st.session_state:
        st.session_state.arrays = {}

    st.title("User Profile Editor")
    user_schema = json_schema["definitions"]["User"]["allOf"][0]
    for category, category_schema in user_schema["properties"].items():

        if "$ref" in category_schema:
            ref_name = category_schema["$ref"].split("/")[-1]
            with st.expander(ref_name, expanded=False):

                st.markdown(f"### Editing: {ref_name}")
                render_form(json_schema["definitions"][ref_name]["allOf"][0], ref_name)
        else:
            with st.expander(category, expanded=False):
                render_form(category_schema, category)

    if st.button("Save JSON"):
        user_data = {}
        user_data["User"] = extract_user_data(user_schema)
        with open("user_model.json", "w") as f:
            json.dump(user_data, f, indent=4)
        st.success("JSON data has been saved as user_data.json")
        st.json(user_data)


if __name__ == "__main__":
    main()
