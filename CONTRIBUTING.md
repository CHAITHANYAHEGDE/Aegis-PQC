# Contributing to Aegis-PQC

First off, thank you for considering contributing to Aegis-PQC! It's people like you that make Aegis-PQC such a great tool for the community.

## 1. Where do I go from here?

If you've noticed a bug or have a feature request, make sure to check our [Issues](https://github.com/CHAITHANYAHEGDE/Aegis-PQC/issues) first to see if someone else has already created a ticket. If not, go ahead and [make one](https://github.com/CHAITHANYAHEGDE/Aegis-PQC/issues/new/choose)!

## 2. Fork & create a branch

If this is something you think you can fix, then fork Aegis-PQC and create a branch with a descriptive name.

## 3. Implement your fix or feature

At this point, you're ready to make your changes! Feel free to ask for help; everyone is a beginner at first.

## 4. Run tests

Please run the test suite to ensure that your changes do not break any existing functionality:
```bash
python phase11_5_pipeline.py
```

## 5. Make a Pull Request

At this point, you should switch back to your master branch and make sure it's up to date with Aegis-PQC's master branch:

```bash
git remote add upstream https://github.com/CHAITHANYAHEGDE/Aegis-PQC.git
git checkout main
git pull upstream main
```

Then update your feature branch from your local copy of main, and push it!

```bash
git checkout <your-branch-name>
git rebase main
git push --set-upstream origin <your-branch-name>
```

Finally, go to GitHub and make a Pull Request.

## 6. Keeping your Pull Request updated

If a maintainer asks you to "rebase" your PR, they're saying that a lot of code has changed, and that you need to update your branch so it's easier to merge.

## 7. Code of Conduct

Please note that this project is released with a [Contributor Code of Conduct](CODE_OF_CONDUCT.md). By participating in this project you agree to abide by its terms.
