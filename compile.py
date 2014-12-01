import os
import logging
import StringIO

from scss import Scss

log = logging.getLogger('PydashieCompiler')
logging.basicConfig()
log.setLevel(logging.INFO)
#Requirements:

#pip install pyScss


#
def main():

    current_directory = os.getcwd()

    logging.info("Compiling from local files ...")
    dashing_dir = os.path.join(current_directory, 'pydashie')
    logging.info("Using walk path : %s" % dashing_dir)

    fileList = []
    for root, subFolders, files in os.walk(dashing_dir):
        for fileName in files:
            if 'scss' in fileName:
                fileList.append(os.path.join(root, fileName))
                log.info('Found SCSS to compile: %s' % fileName)

    css_output = StringIO.StringIO()
    css = Scss()
    css_output.write('\n'.join([css.compile(open(filePath).read()) for filePath in fileList]))

    fileList = []
    for root, subFolders, files in os.walk(dashing_dir):
        for fileName in files:
            if 'css' in fileName and 'scss' not in fileName:
                if (not fileName.endswith('~') and
                        not fileName == "application.css"):
                    # discard any temporary files
                    # ignore the base application.css (duplication issues)
                    fileList.append(os.path.join(root, fileName))
                    log.info('Found CSS to append: %s' % fileName)
    css_output.write('\n'.join([open(filePath).read() for filePath in fileList]))

    app_css_filepath = os.path.join(current_directory,
                                    'pydashie/assets/stylesheets/application.css')
    with open(app_css_filepath, 'w') as outfile:
        outfile.write(css_output.getvalue())
        log.info('Wrote CSS out to : %s' % app_css_filepath)


if __name__ == '__main__':

    main()
