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
          python3 -m coverage run --branch --source . -m pytest  -rf --durations=30 --timeout 60 -v
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
          # build to binary with cxfreeze library, it uses the setup.py and pyproject.toml files
          python3 setup.py build 

          # create the folder structure for the deb package
          # all the files for the program will be in /opt/eyehealth, so easy handle of dependencies
          mkdir -p deb_build/opt/eyehealth 

          # we copy the files from the build folder to the deb package folder before deb creation
          cp -R build/exe.linux-x86_64-3.8/* deb_build/opt/eyehealth

          # we change the permissions of the files and folders because files will keep permissions after packaging
          find deb_build/opt/eyehealth -type f -exec chmod 644 -- {} +
          find deb_build/opt/eyehealth -type d -exec chmod 755 -- {} +

          # we make the binary executable (not done by cxfreeze)
          chmod +x deb_build/opt/eyehealth/eyehealth

          # build the deb package with the official tool
          dpkg-deb --build --root-owner-group deb_build
        '''
      }
    }
    stage('Release') {
      when {
        buildingTag()
      }
      environment {
        VERSION = "$tag_name"
      }
      steps {
        sh """#!/usr/bin/env bash
          set -Eeuxo pipefail

          # rename deb file
          mv deb_build.deb eyehealth-${VERSION}.deb
        """
        script {
          githubUtils.createRelease([
            "eyehealth-${VERSION}.deb"
            ])
        }
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
