FROM kbase/sdkpython:3.8.10
MAINTAINER KBase Developer [Ulas Karaoz (ukaraoz@lbl.gov)]
# -----------------------------------------
# In this section, you can install any system dependencies required
# to run your App.  For instance, you could place an apt-get update or
# install line here, a git checkout to download code, or run any other
# installation scripts.

RUN apt-get update \
	&& apt-get install -y --no-install-recommends \
		r-base \
		r-cran-ggplot2 \
		r-cran-seqinr
RUN R -e "install.packages(c('argparser', 'here'), repos = 'https://cloud.r-project.org')"
# -----------------------------------------

COPY ./ /kb/module
WORKDIR /kb/module

RUN mkdir -p /kb/module/work/tmp/test_data \
    && cp -r /kb/module/test/data/* /kb/module/work/tmp/test_data/ \
    && chmod -R a+rw /kb/module \
    && make all \
    && rm -f /data/__READY__

ENTRYPOINT [ "./scripts/entrypoint.sh" ]

CMD [ ]
