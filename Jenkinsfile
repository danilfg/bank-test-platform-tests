pipeline {
  agent any

  options {
    buildDiscarder(logRotator(numToKeepStr: '10'))
    disableConcurrentBuilds()
  }

  environment {
    TEST_API_BASE_URL = 'http://api-gateway:8080'
    TEST_COMMAND = 'pytest -q'
    ALLURE_VERSION = '2.30.0'
    ALLURE_HOME = '/tmp/allure-2.30.0'
  }

  stages {
    stage('Checkout') {
      steps {
        checkout scm
      }
    }

    stage('Install') {
      steps {
        sh '''#!/bin/bash
          set -euo pipefail

          python3 -m venv .venv
          . .venv/bin/activate
          python -m pip install --upgrade pip

          if [ -f requirements.txt ]; then
            pip install -r requirements.txt
          elif [ -f requerments.txt ]; then
            # Keep the training job forgiving for the common typo.
            pip install -r requerments.txt
          fi

          pip install pytest allure-pytest
        '''
      }
    }

    stage('Tests') {
      steps {
        script {
          env.TEST_EXIT_CODE = sh(
            script: '''#!/bin/bash
              set +e
              . .venv/bin/activate
              export TEST_API_BASE_URL="${TEST_API_BASE_URL:-http://api-gateway:8080}"
              echo "[INFO] TEST_API_BASE_URL=${TEST_API_BASE_URL}"
              eval "${TEST_COMMAND:-pytest -q} --alluredir=allure-results"
              echo $? > .test-exit-code
            ''',
            returnStatus: true
          ).toString()
        }
      }
    }

    stage('Allure HTML') {
      steps {
        sh '''#!/bin/bash
          set -euo pipefail

          if [ ! -x "${ALLURE_HOME}/bin/allure" ]; then
            rm -rf "${ALLURE_HOME}" "/tmp/allure-${ALLURE_VERSION}.tgz"
            curl -fsSL "https://github.com/allure-framework/allure2/releases/download/${ALLURE_VERSION}/allure-${ALLURE_VERSION}.tgz" -o "/tmp/allure-${ALLURE_VERSION}.tgz"
            tar -xzf "/tmp/allure-${ALLURE_VERSION}.tgz" -C /tmp
          fi

          mkdir -p allure-results allure-report
          "${ALLURE_HOME}/bin/allure" generate allure-results -o allure-report --clean || true
        '''
      }
    }
  }

  post {
    always {
      archiveArtifacts artifacts: 'allure-results/**,allure-report/**', allowEmptyArchive: true
      script {
        currentBuild.description = "Allure report: ${env.BUILD_URL}artifact/allure-report/index.html"
        def exitCode = fileExists('.test-exit-code') ? readFile('.test-exit-code').trim() : env.TEST_EXIT_CODE
        if (exitCode && exitCode != '0') {
          currentBuild.result = 'FAILURE'
        }
      }
    }
  }
}
