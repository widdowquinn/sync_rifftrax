# Makefile
#
# Installs (copies) helper scripts to /usr/local/bin

install : srt_postsync srt_presync
	@echo "Installing helper scripts to /usr/local/bin"
	cp ./srt_* /usr/local/bin
