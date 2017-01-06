.PHONY: check
check:
	pep8 species_stat/ --exclude=*/migrations/*
	python `which pylint3` --reports=n `find species_stat/ -name "__init__.py" -not -path "*/migrations/*" | sed -e "s/.__init__.py//"`
