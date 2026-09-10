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
    # pygame is installed above whichever front-end is actually going to be
    # played, so its tests always run - and they open a real display unless SDL
    # is pointed at its dummy drivers. Without these, a machine with no display
    # fails 40 tests and the abort below refuses to start a console game that
    # never needed one. The CI workflow sets the same two.
    #
    # Set on this command only: startProgram launches the game further down, and
    # a dummy video driver exported for the whole script would draw the pygame
    # front-end to nowhere for anyone who has switched INTERFACE_TYPE to it.
    SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3 -m pytest
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
