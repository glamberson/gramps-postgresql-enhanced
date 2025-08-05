# Bulletproof DBAPI Compliance Report

**Generated**: 2025-08-06 00:54:45
**Total Methods**: 266
**Tested**: 266
**Passed**: 255
**Failed**: 11
**Skipped**: 80

**Reliability**: 95.86%

## 🚨 MASSIVE FAILURE
Database is NOT bulletproof. 99% reliability = COMPLETE FAILURE.

## Method Results

| Method | Status | Details |
|--------|--------|--------|
| `add_child_to_family` | ⚠ SKIP | SKIPPED - Potentially dangerous or complex |
| `add_citation` | ⚠ SKIP | SKIPPED - Potentially dangerous or complex |
| `add_event` | ⚠ SKIP | SKIPPED - Potentially dangerous or complex |
| `add_family` | ⚠ SKIP | SKIPPED - Potentially dangerous or complex |
| `add_media` | ⚠ SKIP | SKIPPED - Potentially dangerous or complex |
| `add_note` | ⚠ SKIP | SKIPPED - Potentially dangerous or complex |
| `add_person` | ⚠ SKIP | SKIPPED - Potentially dangerous or complex |
| `add_place` | ⚠ SKIP | SKIPPED - Potentially dangerous or complex |
| `add_repository` | ⚠ SKIP | SKIPPED - Potentially dangerous or complex |
| `add_source` | ⚠ SKIP | SKIPPED - Potentially dangerous or complex |
| `add_tag` | ⚠ SKIP | SKIPPED - Potentially dangerous or complex |
| `add_to_surname_list` | ⚠ SKIP | SKIPPED - Potentially dangerous or complex |
| `cid2user_format` | ✓ PASS | PASSED - formatted: TEST001 |
| `close` | ⚠ SKIP | SKIPPED - Infrastructure method |
| `commit_citation` | ⚠ SKIP | SKIPPED - Potentially dangerous or complex |
| `commit_event` | ⚠ SKIP | SKIPPED - Potentially dangerous or complex |
| `commit_family` | ⚠ SKIP | SKIPPED - Potentially dangerous or complex |
| `commit_media` | ⚠ SKIP | SKIPPED - Potentially dangerous or complex |
| `commit_note` | ⚠ SKIP | SKIPPED - Potentially dangerous or complex |
| `commit_person` | ⚠ SKIP | SKIPPED - Potentially dangerous or complex |
| `commit_place` | ⚠ SKIP | SKIPPED - Potentially dangerous or complex |
| `commit_repository` | ⚠ SKIP | SKIPPED - Potentially dangerous or complex |
| `commit_source` | ⚠ SKIP | SKIPPED - Potentially dangerous or complex |
| `commit_tag` | ⚠ SKIP | SKIPPED - Potentially dangerous or complex |
| `connect` | ⚠ SKIP | SKIPPED - Infrastructure method |
| `db_has_bm_changes` | ⚠ SKIP | SKIPPED - Potentially dangerous or complex |
| `delete_person_from_database` | ⚠ SKIP | SKIPPED - Potentially dangerous or complex |
| `disable_all_signals` | ⚠ SKIP | SKIPPED - Potentially dangerous or complex |
| `disable_logging` | ⚠ SKIP | SKIPPED - Infrastructure method |
| `disable_signals` | ⚠ SKIP | SKIPPED - Potentially dangerous or complex |
| `disconnect` | ⚠ SKIP | SKIPPED - Infrastructure method |
| `disconnect_all` | ⚠ SKIP | SKIPPED - Infrastructure method |
| `eid2user_format` | ✓ PASS | PASSED - formatted: TEST001 |
| `emit` | ⚠ SKIP | SKIPPED - Infrastructure method |
| `enable_all_signals` | ⚠ SKIP | SKIPPED - Potentially dangerous or complex |
| `enable_logging` | ⚠ SKIP | SKIPPED - Infrastructure method |
| `enable_signals` | ⚠ SKIP | SKIPPED - Potentially dangerous or complex |
| `fid2user_format` | ✓ PASS | PASSED - formatted: TEST001 |
| `find_backlink_handles` | ✓ PASS | PASSED - returned generator |
| `find_initial_person` | ✗ FAIL | ERROR: '_class' |
| `find_next_citation_gramps_id` | ✓ PASS | PASSED - returned str |
| `find_next_event_gramps_id` | ✓ PASS | PASSED - returned str |
| `find_next_family_gramps_id` | ✓ PASS | PASSED - returned str |
| `find_next_media_gramps_id` | ✓ PASS | PASSED - returned str |
| `find_next_note_gramps_id` | ✓ PASS | PASSED - returned str |
| `find_next_person_gramps_id` | ✓ PASS | PASSED - returned str |
| `find_next_place_gramps_id` | ✓ PASS | PASSED - returned str |
| `find_next_repository_gramps_id` | ✓ PASS | PASSED - returned str |
| `find_next_source_gramps_id` | ✓ PASS | PASSED - returned str |
| `get_bookmarks` | ✓ PASS | PASSED - returned DbBookmarks |
| `get_child_reference_types` | ✓ PASS | PASSED - returned list |
| `get_citation_bookmarks` | ✓ PASS | PASSED - returned DbBookmarks |
| `get_citation_cursor` | ✓ PASS | PASSED - returned Cursor |
| `get_citation_from_gramps_id` | ✓ PASS | PASSED - returned None |
| `get_citation_from_handle` | ✗ FAIL | ERROR: Handle PERSON001 not found |
| `get_citation_gramps_ids` | ✓ PASS | PASSED - returned list |
| `get_citation_handles` | ✓ PASS | PASSED - returned list |
| `get_dbid` | ✓ PASS | PASSED - returned NoneType |
| `get_dbname` | ✓ PASS | PASSED - returned NoneType |
| `get_default_handle` | ✓ PASS | PASSED - returned NoneType |
| `get_default_person` | ✓ PASS | PASSED - returned NoneType |
| `get_event_attribute_types` | ✓ PASS | PASSED - returned list |
| `get_event_bookmarks` | ✓ PASS | PASSED - returned DbBookmarks |
| `get_event_cursor` | ✓ PASS | PASSED - returned Cursor |
| `get_event_from_gramps_id` | ✓ PASS | PASSED - returned None |
| `get_event_from_handle` | ✗ FAIL | ERROR: Handle PERSON001 not found |
| `get_event_gramps_ids` | ✓ PASS | PASSED - returned list |
| `get_event_handles` | ✓ PASS | PASSED - returned list |
| `get_event_roles` | ✓ PASS | PASSED - returned list |
| `get_event_types` | ✓ PASS | PASSED - returned list |
| `get_family_attribute_types` | ✓ PASS | PASSED - returned list |
| `get_family_bookmarks` | ✓ PASS | PASSED - returned DbBookmarks |
| `get_family_cursor` | ✓ PASS | PASSED - returned Cursor |
| `get_family_event_types` | ✓ PASS | PASSED - returned list |
| `get_family_from_gramps_id` | ✓ PASS | PASSED - returned None |
| `get_family_from_handle` | ✗ FAIL | ERROR: Handle PERSON001 not found |
| `get_family_gramps_ids` | ✓ PASS | PASSED - returned list |
| `get_family_handles` | ✓ PASS | PASSED - returned list |
| `get_family_relation_types` | ✓ PASS | PASSED - returned list |
| `get_feature` | ✓ PASS | PASSED - returned None |
| `get_gender_stats` | ✓ PASS | PASSED - returned dict |
| `get_media_attribute_types` | ✓ PASS | PASSED - returned list |
| `get_media_bookmarks` | ✓ PASS | PASSED - returned DbBookmarks |
| `get_media_cursor` | ✓ PASS | PASSED - returned Cursor |
| `get_media_from_gramps_id` | ✓ PASS | PASSED - returned None |
| `get_media_from_handle` | ✗ FAIL | ERROR: Handle PERSON001 not found |
| `get_media_gramps_ids` | ✓ PASS | PASSED - returned list |
| `get_media_handles` | ✓ PASS | PASSED - returned list |
| `get_mediapath` | ✓ PASS | PASSED - returned NoneType |
| `get_name_group_keys` | ✓ PASS | PASSED - returned list |
| `get_name_group_mapping` | ✓ PASS | PASSED - returned TestSurname |
| `get_name_types` | ✓ PASS | PASSED - returned list |
| `get_note_bookmarks` | ✓ PASS | PASSED - returned DbBookmarks |
| `get_note_cursor` | ✓ PASS | PASSED - returned Cursor |
| `get_note_from_gramps_id` | ✓ PASS | PASSED - returned None |
| `get_note_from_handle` | ✗ FAIL | ERROR: Handle PERSON001 not found |
| `get_note_gramps_ids` | ✓ PASS | PASSED - returned list |
| `get_note_handles` | ✓ PASS | PASSED - returned list |
| `get_note_types` | ✓ PASS | PASSED - returned list |
| `get_number_of_citations` | ✓ PASS | PASSED - returned int |
| `get_number_of_events` | ✓ PASS | PASSED - returned int |
| `get_number_of_families` | ✓ PASS | PASSED - returned int |
| `get_number_of_media` | ✓ PASS | PASSED - returned int |
| `get_number_of_notes` | ✓ PASS | PASSED - returned int |
| `get_number_of_people` | ✓ PASS | PASSED - returned int |
| `get_number_of_places` | ✓ PASS | PASSED - returned int |
| `get_number_of_repositories` | ✓ PASS | PASSED - returned int |
| `get_number_of_sources` | ✓ PASS | PASSED - returned int |
| `get_number_of_tags` | ✓ PASS | PASSED - returned int |
| `get_origin_types` | ✓ PASS | PASSED - returned list |
| `get_person_attribute_types` | ✓ PASS | PASSED - returned list |
| `get_person_cursor` | ✓ PASS | PASSED - returned Cursor |
| `get_person_event_types` | ✓ PASS | PASSED - returned list |
| `get_person_from_gramps_id` | ✓ PASS | PASSED - returned Person |
| `get_person_from_handle` | ✓ PASS | PASSED - returned Person |
| `get_person_gramps_ids` | ✓ PASS | PASSED - returned list |
| `get_person_handles` | ✓ PASS | PASSED - returned list |
| `get_place_bookmarks` | ✓ PASS | PASSED - returned DbBookmarks |
| `get_place_cursor` | ✓ PASS | PASSED - returned Cursor |
| `get_place_from_gramps_id` | ✓ PASS | PASSED - returned None |
| `get_place_from_handle` | ✗ FAIL | ERROR: Handle PERSON001 not found |
| `get_place_gramps_ids` | ✓ PASS | PASSED - returned list |
| `get_place_handles` | ✓ PASS | PASSED - returned list |
| `get_place_tree_cursor` | ✓ PASS | PASSED - returned Cursor |
| `get_place_types` | ✓ PASS | PASSED - returned list |
| `get_raw_citation_data` | ✓ PASS | PASSED - returned None |
| `get_raw_event_data` | ✓ PASS | PASSED - returned None |
| `get_raw_family_data` | ✓ PASS | PASSED - returned None |
| `get_raw_media_data` | ✓ PASS | PASSED - returned None |
| `get_raw_note_data` | ✓ PASS | PASSED - returned None |
| `get_raw_person_data` | ✓ PASS | PASSED - returned DataDict |
| `get_raw_place_data` | ✓ PASS | PASSED - returned None |
| `get_raw_repository_data` | ✓ PASS | PASSED - returned None |
| `get_raw_source_data` | ✓ PASS | PASSED - returned None |
| `get_raw_tag_data` | ✓ PASS | PASSED - returned None |
| `get_repo_bookmarks` | ✓ PASS | PASSED - returned DbBookmarks |
| `get_repository_cursor` | ✓ PASS | PASSED - returned Cursor |
| `get_repository_from_gramps_id` | ✓ PASS | PASSED - returned None |
| `get_repository_from_handle` | ✗ FAIL | ERROR: Handle PERSON001 not found |
| `get_repository_gramps_ids` | ✓ PASS | PASSED - returned list |
| `get_repository_handles` | ✓ PASS | PASSED - returned list |
| `get_repository_types` | ✓ PASS | PASSED - returned list |
| `get_researcher` | ✓ PASS | PASSED - returned Researcher |
| `get_save_path` | ✓ PASS | PASSED - returned NoneType |
| `get_schema_version` | ✓ PASS | PASSED - returned int |
| `get_source_attribute_types` | ✓ PASS | PASSED - returned list |
| `get_source_bookmarks` | ✓ PASS | PASSED - returned DbBookmarks |
| `get_source_cursor` | ✓ PASS | PASSED - returned Cursor |
| `get_source_from_gramps_id` | ✓ PASS | PASSED - returned None |
| `get_source_from_handle` | ✗ FAIL | ERROR: Handle PERSON001 not found |
| `get_source_gramps_ids` | ✓ PASS | PASSED - returned list |
| `get_source_handles` | ✓ PASS | PASSED - returned list |
| `get_source_media_types` | ✓ PASS | PASSED - returned list |
| `get_summary` | ✓ PASS | PASSED - returned dict |
| `get_surname_list` | ✓ PASS | PASSED - returned list |
| `get_tag_cursor` | ✓ PASS | PASSED - returned Cursor |
| `get_tag_from_handle` | ✗ FAIL | ERROR: Handle PERSON001 not found |
| `get_tag_from_name` | ✓ PASS | PASSED - returned None |
| `get_tag_handles` | ✓ PASS | PASSED - returned list |
| `get_total` | ✓ PASS | PASSED - returned int |
| `get_undodb` | ✓ PASS | PASSED - returned DbGenericUndo |
| `get_url_types` | ✓ PASS | PASSED - returned list |
| `has_citation_gramps_id` | ✓ PASS | PASSED - returned False |
| `has_citation_handle` | ✓ PASS | PASSED - returned False |
| `has_event_gramps_id` | ✓ PASS | PASSED - returned False |
| `has_event_handle` | ✓ PASS | PASSED - returned False |
| `has_family_gramps_id` | ✓ PASS | PASSED - returned False |
| `has_family_handle` | ✓ PASS | PASSED - returned False |
| `has_media_gramps_id` | ✓ PASS | PASSED - returned False |
| `has_media_handle` | ✓ PASS | PASSED - returned False |
| `has_name_group_key` | ✓ PASS | PASSED - returned None |
| `has_note_gramps_id` | ✓ PASS | PASSED - returned False |
| `has_note_handle` | ✓ PASS | PASSED - returned False |
| `has_person_gramps_id` | ✓ PASS | PASSED - returned False |
| `has_person_handle` | ✓ PASS | PASSED - returned False |
| `has_place_gramps_id` | ✓ PASS | PASSED - returned False |
| `has_place_handle` | ✓ PASS | PASSED - returned False |
| `has_repository_gramps_id` | ✓ PASS | PASSED - returned False |
| `has_repository_handle` | ✓ PASS | PASSED - returned False |
| `has_source_gramps_id` | ✓ PASS | PASSED - returned False |
| `has_source_handle` | ✓ PASS | PASSED - returned False |
| `has_tag_handle` | ✓ PASS | PASSED - returned False |
| `id2user_format` | ✓ PASS | PASSED - formatted: TEST001 |
| `is_open` | ✓ PASS | PASSED - returned bool |
| `iter_citation_handles` | ✓ PASS | PASSED - iterator works |
| `iter_citations` | ✓ PASS | PASSED - iterator works |
| `iter_event_handles` | ✓ PASS | PASSED - iterator works |
| `iter_events` | ✓ PASS | PASSED - iterator works |
| `iter_families` | ✓ PASS | PASSED - iterator works |
| `iter_family_handles` | ✓ PASS | PASSED - iterator works |
| `iter_media` | ✓ PASS | PASSED - iterator works |
| `iter_media_handles` | ✓ PASS | PASSED - iterator works |
| `iter_note_handles` | ✓ PASS | PASSED - iterator works |
| `iter_notes` | ✓ PASS | PASSED - iterator works |
| `iter_people` | ✓ PASS | PASSED - empty iterator |
| `iter_person_handles` | ✓ PASS | PASSED - iterator works |
| `iter_place_handles` | ✓ PASS | PASSED - iterator works |
| `iter_places` | ✓ PASS | PASSED - iterator works |
| `iter_repositories` | ✓ PASS | PASSED - iterator works |
| `iter_repository_handles` | ✓ PASS | PASSED - iterator works |
| `iter_source_handles` | ✓ PASS | PASSED - iterator works |
| `iter_sources` | ✓ PASS | PASSED - iterator works |
| `iter_tag_handles` | ✓ PASS | PASSED - iterator works |
| `iter_tags` | ✓ PASS | PASSED - iterator works |
| `load` | ⚠ SKIP | SKIPPED - Potentially dangerous or complex |
| `log_all` | ⚠ SKIP | SKIPPED - Infrastructure method |
| `marriage_from_eventref_list` | ⚠ SKIP | SKIPPED - Potentially dangerous or complex |
| `method` | ⚠ SKIP | SKIPPED - Infrastructure method |
| `nid2user_format` | ✓ PASS | PASSED - formatted: TEST001 |
| `oid2user_format` | ✓ PASS | PASSED - formatted: TEST001 |
| `pid2user_format` | ✓ PASS | PASSED - formatted: TEST001 |
| `rebuild_secondary` | ⚠ SKIP | SKIPPED - Potentially dangerous or complex |
| `redo` | ⚠ SKIP | SKIPPED - Potentially dangerous or complex |
| `reindex_reference_map` | ⚠ SKIP | SKIPPED - Potentially dangerous or complex |
| `remove_child_from_family` | ⚠ SKIP | SKIPPED - Potentially dangerous or complex |
| `remove_citation` | ⚠ SKIP | SKIPPED - Potentially dangerous or complex |
| `remove_event` | ⚠ SKIP | SKIPPED - Potentially dangerous or complex |
| `remove_family` | ⚠ SKIP | SKIPPED - Potentially dangerous or complex |
| `remove_family_relationships` | ⚠ SKIP | SKIPPED - Potentially dangerous or complex |
| `remove_from_surname_list` | ⚠ SKIP | SKIPPED - Potentially dangerous or complex |
| `remove_media` | ⚠ SKIP | SKIPPED - Potentially dangerous or complex |
| `remove_note` | ⚠ SKIP | SKIPPED - Potentially dangerous or complex |
| `remove_parent_from_family` | ⚠ SKIP | SKIPPED - Potentially dangerous or complex |
| `remove_person` | ⚠ SKIP | SKIPPED - Potentially dangerous or complex |
| `remove_place` | ⚠ SKIP | SKIPPED - Potentially dangerous or complex |
| `remove_repository` | ⚠ SKIP | SKIPPED - Potentially dangerous or complex |
| `remove_source` | ⚠ SKIP | SKIPPED - Potentially dangerous or complex |
| `remove_tag` | ⚠ SKIP | SKIPPED - Potentially dangerous or complex |
| `report_bm_change` | ⚠ SKIP | SKIPPED - Potentially dangerous or complex |
| `request_rebuild` | ⚠ SKIP | SKIPPED - Potentially dangerous or complex |
| `requires_login` | ⚠ SKIP | SKIPPED - Infrastructure method |
| `reset` | ⚠ SKIP | SKIPPED - Potentially dangerous or complex |
| `rid2user_format` | ✓ PASS | PASSED - formatted: TEST001 |
| `save_gender_stats` | ⚠ SKIP | SKIPPED - Potentially dangerous or complex |
| `set_birth_death_index` | ⚠ SKIP | SKIPPED - Potentially dangerous or complex |
| `set_citation_id_prefix` | ✓ PASS | PASSED - prefix set |
| `set_default_person_handle` | ⚠ SKIP | SKIPPED - Potentially dangerous or complex |
| `set_event_id_prefix` | ✓ PASS | PASSED - prefix set |
| `set_family_id_prefix` | ✓ PASS | PASSED - prefix set |
| `set_feature` | ⚠ SKIP | SKIPPED - Potentially dangerous or complex |
| `set_media_id_prefix` | ✓ PASS | PASSED - prefix set |
| `set_mediapath` | ⚠ SKIP | SKIPPED - Potentially dangerous or complex |
| `set_name_group_mapping` | ⚠ SKIP | SKIPPED - Potentially dangerous or complex |
| `set_note_id_prefix` | ✓ PASS | PASSED - prefix set |
| `set_person_id_prefix` | ✓ PASS | PASSED - prefix set |
| `set_place_id_prefix` | ✓ PASS | PASSED - prefix set |
| `set_prefixes` | ✗ FAIL | ERROR: DbGeneric.set_prefixes() missing 1 required positional argument: 'note' |
| `set_repository_id_prefix` | ✓ PASS | PASSED - prefix set |
| `set_researcher` | ⚠ SKIP | SKIPPED - Potentially dangerous or complex |
| `set_schema_version` | ⚠ SKIP | SKIPPED - Potentially dangerous or complex |
| `set_serializer` | ⚠ SKIP | SKIPPED - Potentially dangerous or complex |
| `set_source_id_prefix` | ✓ PASS | PASSED - prefix set |
| `set_text` | ⚠ SKIP | SKIPPED - Infrastructure method |
| `set_total` | ⚠ SKIP | SKIPPED - Potentially dangerous or complex |
| `sid2user_format` | ✓ PASS | PASSED - formatted: TEST001 |
| `transaction_abort` | ⚠ SKIP | SKIPPED - Potentially dangerous or complex |
| `transaction_begin` | ⚠ SKIP | SKIPPED - Potentially dangerous or complex |
| `transaction_commit` | ⚠ SKIP | SKIPPED - Potentially dangerous or complex |
| `undo` | ⚠ SKIP | SKIPPED - Potentially dangerous or complex |
| `undo_data` | ⚠ SKIP | SKIPPED - Potentially dangerous or complex |
| `undo_reference` | ⚠ SKIP | SKIPPED - Potentially dangerous or complex |
| `update_empty` | ⚠ SKIP | SKIPPED - Potentially dangerous or complex |
| `update_real` | ⚠ SKIP | SKIPPED - Potentially dangerous or complex |
| `upgrade_table_for_json_data` | ⚠ SKIP | SKIPPED - Potentially dangerous or complex |
| `use_json_data` | ✓ PASS | PASSED - returned bool |
| `version_supported` | ✓ PASS | PASSED - returned bool |
