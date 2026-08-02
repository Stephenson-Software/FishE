# /bin/bash
# Usage: ./run.sh

getLatest() {
    # get the latest version of the code
    echo "Pulling latest version of code from GitHub"
    git pull
    echo ""
}

printBranchStatus() {
    # print the current branch
    echo "Current branch: $(git branch --show-current)"
    echo ""
}

printVersion() {
    # print the current version
    echo "Current version: $(cat version.txt)"
    echo ""
}

checkDependencies() {
    # check that dependencies are installed
    echo "Checking dependencies"
    if ! command -v python3 &> /dev/null
    then
        echo "Python could not be found. Download it from https://www.python.org/downloads/"
        exit 1
    fi
    if ! command -v pip &> /dev/null
    then
        echo "Pip could not be found. Download it from https://pip.pypa.io/en/stable/installation/ or run 'python -m ensurepip' in a terminal"
        exit 1
    fi
    pip install pygame --pre --quiet
    pip install pytest --quiet
    pip install -r requirements.txt --quiet
    echo ""
}

runTests() {
    # run tests
    echo "Running tests"
    python3 -m pytest
    testExitCode=$?
    echo ""
    if [ $testExitCode -ne 0 ]; then
        echo "Tests failed. Aborting."
        exit $testExitCode
    fi
}

startProgram() {
    # start program
    echo "Starting program"
    python3 src/fishE.py
}

# main
getLatest
printBranchStatus
printVersion
checkDependencies
runTests
startProgram
