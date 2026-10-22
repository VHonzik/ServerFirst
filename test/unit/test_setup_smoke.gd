extends GutTest


func test_headless_runtime() -> void:
	assert_eq(DisplayServer.get_name(), "headless")
	assert_eq(ProjectSettings.get_setting("application/config/name"), "Server First")


func test_user_data_round_trip() -> void:
	var data_root := OS.get_environment("APPDATA").replace("\\", "/").to_lower()
	var user_directory := OS.get_user_data_dir().replace("\\", "/").to_lower()
	assert_false(data_root.is_empty(), "Validation must provide workspace-local user paths")
	assert_true(user_directory.begins_with(data_root + "/"), "user:// must stay under APPDATA")
	var path := "user://setup-smoke.txt"
	var output := FileAccess.open(path, FileAccess.WRITE)
	assert_not_null(output, "user:// must be writable")
	if output == null:
		return
	output.store_string("Server First headless smoke")
	output.close()
	assert_eq(FileAccess.get_file_as_string(path), "Server First headless smoke")
	assert_eq(DirAccess.remove_absolute(ProjectSettings.globalize_path(path)), OK)
