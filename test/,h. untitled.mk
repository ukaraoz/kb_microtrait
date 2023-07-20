build-test-script:
    echo '#!/bin/bash' > $(TEST_DIR)/$(TEST_SCRIPT_NAME)
    echo 'script_dir=$$(dirname "$$(readlink -f "$$0")")' >> $(TEST_DIR)/$(TEST_SCRIPT_NAME)
    echo 'export KB_DEPLOYMENT_CONFIG=$$script_dir/../deploy.cfg' >> $(TEST_DIR)/$(TEST_SCRIPT_NAME)
    echo 'export KB_AUTH_TOKEN=`cat /kb/module/work/token`' >> $(TEST_DIR)/$(TEST_SCRIPT_NAME)
    echo 'echo "Removing temp files..."' >> $(TEST_DIR)/$(TEST_SCRIPT_NAME)
    echo 'rm -rf $(WORK_DIR)/*' >> $(TEST_DIR)/$(TEST_SCRIPT_NAME)
    echo 'echo "...done removing temp files."' >> $(TEST_DIR)/$(TEST_SCRIPT_NAME)
    echo 'export PYTHONPATH=$$script_dir/../$(LIB_DIR):$$PATH:$$PYTHONPATH' >> $(TEST_DIR)/$(TEST_SCRIPT_NAME)
    echo 'cd $$script_dir/../$(TEST_DIR)' >> $(TEST_DIR)/$(TEST_SCRIPT_NAME)
    echo 'python -m nose --with-coverage --cover-package=$(SERVICE_CAPS) --cover-html --cover-html-dir=/kb/module/work/test_coverage --nocapture  --nologcapture .' >> $(TEST_DIR)/$(TEST_SCRIPT_NAME)
    chmod +x $(TEST_DIR)/$(TEST_SCRIPT_NAME)

saved_assembly = self.au.save_assembly_from_fasta({
            'file': {'path': assembly_file_path},
            'workspace_name': self.ws_info[1],
            'assembly_name': assembly['name'],
        })
 self._client = _BaseClient(
            url, timeout=timeout, user_id=user_id, password=password,
            token=token, ignore_authrc=ignore_authrc,
            trust_all_ssl_certificates=trust_all_ssl_certificates,
            auth_svc=auth_svc,
            async_job_check_time_ms=async_job_check_time_ms,
            async_job_check_time_scale_percent=async_job_check_time_scale_percent,
            async_job_check_max_time_ms=async_job_check_max_time_ms)

 saved_assembly_set = self.setAPI.save_assembly_set_v1({
            'workspace_name': self.ws_info[1],
            'output_object_name': assemblyset['name'],
            'data': {
                'description': 'test assembly set',
                'items': assemblyset['items'],
            },
        })
 