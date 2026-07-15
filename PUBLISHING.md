# Publishing

This repository is prepared for GitHub under:

```text
hcwang001/afe-analog-design-flow
```

## License

This repository uses the MIT License. Keep the `LICENSE` file in the repository
root when publishing or mirroring the project.

## Publish With GitHub CLI

Install Git and GitHub CLI, then run:

```powershell
cd C:\Users\whc\Documents\AFE\github\afe-analog-design-flow
git init
git add .
git commit -m "Initial neural recording AFE design flow skill"
gh auth login
gh repo create hcwang001/afe-analog-design-flow --public --source . --remote origin --push
```

Use `--private` instead of `--public` if the repository should be private.

## Publish With Existing Empty GitHub Repo

If you create the repository manually on GitHub first:

```powershell
cd C:\Users\whc\Documents\AFE\github\afe-analog-design-flow
git init
git add .
git commit -m "Initial neural recording AFE design flow skill"
git branch -M main
git remote add origin https://github.com/hcwang001/afe-analog-design-flow.git
git push -u origin main
```

## Post-Publish Checks

After GitHub renders the repo:

- Confirm README images display.
- Confirm `skills/afe-analog-design-flow/SKILL.md` is visible.
- Confirm no PDK/model/PEX/raw simulation files were uploaded.
- Confirm no template contains approved state, completed review, active waiver
  authorization, or simulated human signature.
- Run `python -m unittest discover -s skills/afe-analog-design-flow/tests -v`.
- Treat publication review separately from project gate review.

## Contact

Maintainer: HC Wang  
Email: [hcwang@hdu.edu.cn](mailto:hcwang@hdu.edu.cn)
