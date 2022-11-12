pipeline {
    agent { label 'master' }
    stages {
        stage('build') {
            steps {
                script {
                    def disk_size = sh(script: "df / --output=avail | tail -1", returnStdout: true).trim() as Integer
                    println("disk_size = ${disk_size}")
                }
            }
        }
    }
}


pipeline {
    agent any
    steps {
        step('Get Build Numbers') {
            script {
                def version_numbers = bat(script: 'python get_version_numbers.py', returnStdout: true)
                def versions_as_array = version_numbers.split('\n')
            }
        }
    }
}

def String myVar

stage('my-first-stage') {
  myVar = sh(script: 'my-command', returnStdout: true)
}

stage('my-second-stage') {
  sh("my-other-command --var='${myVar}'")
}

pipeline {
  agent { label 'docker' }
  stages {
    stage('one') {
      steps {
        sh 'echo hotness > myfile.txt'
        script {
          // trim removes leading and trailing whitespace from the string
          myVar = readFile('myfile.txt').trim()
        }
        echo "${myVar}" // prints 'hotness'
      }
    }
    stage('two') {
      steps {
        echo "${myVar}" // prints 'hotness'
      }
    }
    // this stage is skipped due to the when expression, so nothing is printed
    stage('three') {
      when {
        expression { myVar != 'hotness' }
      }
      steps {
        echo "three: ${myVar}"
      }
    }
  }
}
script{
  sh " 'shell command here' > command"
  command_var = readFile('command').trim()
  sh "export command_var=$command_var"
}

dfhapiefwhkfbaij
//         stage('test the ebfile of modulename is exit or not??') {
//             steps {
// //                 script{
// //                     sh '''
// // ls -lh /fuyun
// // su  fydev  -c \' whoami  && \\
// // source /usr/share/lmod/lmod/init/bash && \\
// // module load Python/3.7.4-GCCcore-8.3.0 && \\
// // python file_exit.py \'
// // '''
// //                     println("${env.flag}")
// //                 }
//                 // script {
//                 //     def test_file = "${env.COMMITMES}"
//                 //     echo "${test_file}"
//                 //     /* groovylint-disable-next-line SpaceAfterClosingBrace */
//                 //     if(fileExists(${test_file}) == true) {
//                 //         echo('test file is exists !!!!!')
//                 //     }else{
//                 //         echo('test file not found !!!')
//                 //     }


//                 // }
//             }
//         }
*******************************************************
pipeline {
    stages {
        stage('This is a Level 1 Stage') {
            stages {
                stage(This is a level 2 stage') { steps{...} }
                stage(This is a level 2 stage') { steps{...} }
                stage(This is a level 2 stage') { steps{...} }
            }
        }
        stage('This is a Level 1 Stage') {
            stages {
                stage(This is a level 2 stage') { steps{...} }
                stage(This is a level 2 stage') { steps{...} }
                stage(This is a level 2 stage') { steps{...} }
            }
        }
    }
}
pipeline {
    agent any
    parameters {
        string (
            defaultValue: '*',
            description: '',
            name : 'BRANCH_PATTERN')
        booleanParam (
            defaultValue: false,
            description: '',
            name : 'FORCE_FULL_BUILD')
    }

    stages {
        stage ('Prepare') {
            steps {
                checkout([$class: 'GitSCM',
                    branches: [[name: "origin/${BRANCH_PATTERN}"]],
                    doGenerateSubmoduleConfigurations: false,
                    extensions: [[$class: 'LocalBranch']],
                    submoduleCfg: [],
                    userRemoteConfigs: [[
                        credentialsId: 'bitwiseman_github',
                        url: 'https://github.com/bitwiseman/hermann']]])
            }
        }

        stage ('Build') {
            when {
                expression {
                    GIT_BRANCH = 'origin/' + sh(returnStdout: true, script: 'git rev-parse --abbrev-ref HEAD').trim()
                    return GIT_BRANCH == 'origin/master' || params.FORCE_FULL_BUILD
                }
            }
            steps {
                // Freestyle build trigger calls a list of jobs
                // Pipeline build() step only calls one job
                // To run all three jobs in parallel, we use "parallel" step
                // https://jenkins.io/doc/pipeline/examples/#jobs-in-parallel
                parallel (
                    linux: {
                        build job: 'full-build-linux', parameters: [string(name: 'GIT_BRANCH_NAME', value: GIT_BRANCH)]
                    },
                    mac: {
                        build job: 'full-build-mac', parameters: [string(name: 'GIT_BRANCH_NAME', value: GIT_BRANCH)]
                    },
                    windows: {
                        build job: 'full-build-windows', parameters: [string(name: 'GIT_BRANCH_NAME', value: GIT_BRANCH)]
                    },
                    failFast: false)
            }
        }
        stage ('Build Skipped') {
            when {
                expression {
                    GIT_BRANCH = 'origin/' + sh(returnStdout: true, script: 'git rev-parse --abbrev-ref HEAD').trim()
                    return !(GIT_BRANCH == 'origin/master' || params.FORCE_FULL_BUILD)
                }
            }
            steps {
                echo 'Skipped full build.'
            }
        }
    }
}