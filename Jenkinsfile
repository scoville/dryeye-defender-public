#!/usr/bin/env groovy

library 'scoville-jenkins-libs'

pipeline {

  options {
    ansiColor('xterm')
  }

  environment {
    PYTHON_MODULES = 'eyeblink_gui tests'
  }

  agent {
    dockerfile {
      filename './Dockerfile'
      additionalBuildArgs '--build-arg USER_ID=${USER_ID} --build-arg GROUP_ID=${GROUP_ID}' \
        + ' --build-arg AUX_GROUP_IDS="${AUX_GROUP_IDS}"'
    }
  }

  stages {

    stage('Lint') {

      steps {
        sh """#!/usr/bin/env bash
          set -Eeux
          python3 -m pylint ${PYTHON_MODULES} |& tee pylint.log
          echo "\${PIPESTATUS[0]}" | tee pylint_status.log
          python3 -m mypy ${PYTHON_MODULES} |& tee mypy.log
          echo "\${PIPESTATUS[0]}" | tee mypy_status.log
          python3 -m pycodestyle ${PYTHON_MODULES} |& tee pycodestyle.log
          echo "\${PIPESTATUS[0]}" | tee pycodestyle_status.log
          python -m pydocstyle ${PYTHON_MODULES} |& tee pydocstyle.log
          echo "\${PIPESTATUS[0]}" | tee pydocstyle_status.log
          """
      }
    }

    stage('Test') {
      steps {
        sh '''#!/usr/bin/env bash
          set -Eeuxo pipefail
          python3 -m coverage run --branch --source . -m pytest -v
        '''
      }
    }

    stage('Coverage') {
      steps {
        sh '''#!/usr/bin/env bash
          set -Eeux
          python3 -m coverage report --show-missing |& tee coverage.log
          echo "${PIPESTATUS[0]}" | tee coverage_status.log
        '''
      }
    }
    stage('Build') {
      steps {
        sh '''#!/usr/bin/env bash
          set -Eeux
          python3 setup.py build
        '''
      }
    }

  }

  post {
    unsuccessful {
      script {
        defaultHandlers.afterBuildFailed()
      }
    }
    regression {
      script {
        defaultHandlers.afterBuildBroken()
      }
    }
    fixed {
      script {
        defaultHandlers.afterBuildFixed()
      }
    }
    always {
      script {
        defaultHandlers.afterPythonBuild()
      }
    }
  }

}
