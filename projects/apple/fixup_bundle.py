#!/usr/bin/env python


#App="$1" # argument is the application to fixup
#LibrariesPrefix="Contents/Libraries"
#echo ""
#echo "Fixing up $App"
#echo "All required frameworks/libraries will be placed under $App/$LibrariesPrefix"
#echo ""
#echo "----------------------------"
#echo "Locating all executables and dylibs already in the package ... "
#
## the sed-call removes the : Mach-O.. suffix that "file" generates
#executables=`find $App | xargs file | grep -i "Mach-O.*executable" | sed "s/:.*//" | sort`
#
#echo "----------------------------"
#echo "Found following executables:"
#for i in $executables; do
#  echo $i
#done
#
## for each executable, find any external library.
#
#
#libraries=`find $App | xargs file | grep -i "Mach-O.*shared library" | sed "s/:.*//" | sort`
#
## command to find all external libraries referrenced in package:
## find paraview.app | xargs file | grep "Mach-O" | sed "s/:.*//" | xargs otool -l | grep " name" | sort | uniq | sed "s/name\ //" | grep -v "@executable"
#
## find non-system libs
## find paraview.app | xargs file | grep "Mach-O" | sed "s/:.*//" | xargs otool -l | grep " name" | sort | uniq | sed "s/name\ //" | grep -v "@executable" | grep -v "/System/" | grep -v "/usr/lib/"

import commands
import sys
import os.path
import re
import shutil

class Library(object):
  def __init__(self):
    # This is the actual path to a physical file
    self.RealPath = None

    # This is the id for shared library.
    self.Id = None

    # These are names for symbolic links to this file.
    self.SymLinks = []

    # This is a symlink to the library that may have been used in other libraries' otool -L output
    self.LinkPath = None

    self.__depencies = None
    pass

  def __hash__(self):
    return self.RealPath.__hash__()

  def __eq__(self, other):
    return self.RealPath == other.RealPath

  def __repr__(self):
    return "Library(%s : %s)" % (self.Id, self.RealPath)

  def dependencies(self, exepath):
    if self.__depencies:
      return self.__depencies
    collection = set()
    for dep in _getdependencies(self.RealPath):
      collection.add(Library.createFromReference(dep, exepath))
    self.__depencies = collection
    return self.__depencies

  def copyToApp(self, app, fakeCopy=False):
    if _isframework(self.RealPath):
      m = re.match(r'(.*)/(\w+\.framework)/(.*)', self.RealPath)
      # FIXME: this could be optimized to only copy the particular version.
      if not fakeCopy:
        print "Copying %s/%s ==> %s" % (m.group(1), m.group(2), ".../Contents/Frameworks/")
        dirdest = os.path.join(os.path.join(app, "Contents/Frameworks/"), m.group(2))
        filedest = os.path.join(dirdest, m.group(3))
        shutil.copytree(os.path.join(m.group(1), m.group(2)), dirdest, symlinks=True)
      self.Id = "@executable_path/../Frameworks/%s" % (os.path.join(m.group(2), m.group(3)))
      #print self.Id, dirdest, filedest
      if not fakeCopy:
        commands.getoutput('install_name_tool -id "%s" %s' % (self.Id, filedest))
    else:
      if not fakeCopy:
        print "Copying %s ==> %s" % (self.RealPath, ".../Contents/Libraries/%s" % os.path.basename(self.RealPath))
        shutil.copy(self.RealPath, os.path.join(app, "Contents/Libraries"))
      self.Id = "@executable_path/../Libraries/%s" % os.path.basename(self.RealPath)
      if not fakeCopy:
        # Sometimes the library can't be modified due to it original permissions... fix them
        import stat
        os.chmod(os.path.join(app, "Contents/Libraries/%s" % os.path.basename(self.RealPath)),\
                 stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
        commands.getoutput('install_name_tool -id "%s" %s' % (self.Id,
                            os.path.join(app, "Contents/Libraries/%s" % os.path.basename(self.RealPath))))

      # Create symlinks for this copied file in the install location
      # as were present in the source dir.
      destdir = os.path.join(app, "Contents/Libraries")
      # sourcefile is the file we copied already into the app bundle. We need to create symlink
      # to it itself in the app bundle.
      sourcefile = os.path.basename(self.RealPath)
      for symlink in self.SymLinks:
        print "Creating Symlink %s ==> .../Contents/Libraries/%s" % (symlink, os.path.basename(self.RealPath))
        if not fakeCopy:
          commands.getoutput("ln -s %s %s" % (sourcefile, os.path.join(destdir, symlink)))

  @classmethod
  def createFromReference(cls, ref, exepath):
    path = ref.replace("@executable_path", exepath)
    if not os.path.exists(path):
      path = _find(ref)
    return cls.createFromPath(path)

  @classmethod
  def createFromPath(cls, path):
    if not os.path.exists(path):
      raise RuntimeError, "%s is not a filename" % path
    lib = Library()
    lib.RealPath = os.path.realpath(path)
    lib.Id = _getid(path)
    if not os.path.abspath(path) == lib.Id:
        lib.LinkPath = os.path.abspath(path)
    elif lib.RealPath != lib.Id:
        lib.LinkPath = lib.RealPath
    # locate all symlinks to this file in the containing directory. These are used when copying.
    # We ensure that we copy all symlinks too.
    dirname = os.path.dirname(lib.RealPath)
    symlinks = commands.getoutput("find -L %s -samefile %s" % (dirname, lib.RealPath))
    symlinks = symlinks.split()
    try:
      symlinks.remove(lib.RealPath)
    except ValueError:
      pass
    linknames = []
    for link in symlinks:
      linkname = os.path.basename(link)
      linknames.append(linkname)
    lib.SymLinks = linknames
    return lib


def _getid(lib):
  """Returns the id for the library"""
  val = commands.getoutput("otool -D %s" % lib)
  m = re.match(r"[^:]+:\s*([^\s]+)", val)
  if m:
    return m.group(1)
  raise RuntimeError, "Could not determine id for %s" % lib

def _getdependencies(path):
  val = commands.getoutput('otool -l %s| grep " name" | sort | uniq | sed "s/name\ //" | sed "s/(offset.*)//"' % path)
  return val.split()

def isexcluded(id):
  # we don't consider the libgfortran or libquadmath a system library since
  # it will rarely be on the installed machine
  # libgfortran depends on libgcc_s, so that one also should not be considered
  # a system library
  if re.match(r".*libgfortran.*", id) or re.match(r".*libquadmath.*", id) or re.match(r".*libgcc_s.*", id):
    return False
  if re.match(r"^/System/Library", id):
    return True
  if re.match(r"^/usr/lib", id):
    return True
  if re.match(r"^/usr/local", id):
    return True
  if re.match(r"^libz.1.dylib", id):
    return True
  return False

def _isframework(path):
  if re.match(".*\.framework.*", path):
    return True

def _find(ref):
  name = os.path.basename(ref)
  for loc in SearchLocations:
    output = commands.getoutput('find "%s" -name "%s"' % (loc, name)).strip()
    if output and '\n' in output:
      files = output.split('\n')
      fileinfo = [ (f, commands.getoutput('file %s | grep -i "Mach-O"' % (f,))) for f in files]
      libfiles = [ f[0] for f in fileinfo if len(f[1]) > 0]
      if len(libfiles) > 0:
        return libfiles[0] # And hope it is the right one
    if output:
      return output
  return ref

SearchLocations = []
if __name__ == "__main__":
  import argparse
  parser = argparse.ArgumentParser()
  parser.add_argument('--exe', dest='app', required=True, help="The executable to fixup")
  parser.add_argument('--search', dest='searchPaths', required=True, action='append', help='Paths to search for libraries not in the bundle')
  parser.add_argument('--plugins',  dest='pluginDir', help='Directory that contains Qt plugins')
  config = parser.parse_args()
  App = config.app
  SearchLocations = config.searchPaths
  QtPluginsDir = config.pluginDir
  LibrariesPrefix = "Contents/Libraries"

  print "------------------------------------------------------------"
  print "Fixing up ",App
  print "All required frameworks/libraries will be placed under %s/%s" % (App, LibrariesPrefix)
  print ""

  executables = commands.getoutput('find %s -type f| xargs file | grep -i "Mach-O.*executable" | sed "s/:.*//" | cut -d\\  -f1 | sort' % App)
  executables = executables.split()
  print "------------------------------------------------------------"
  print "Found executables : "
  for exe in executables:
    print "    %s/%s" % (os.path.basename(App) ,os.path.relpath(exe, App))
  print ""

  # If Qt Plugins dir is specified, copies those in right now.
  # We need to fix paths on those too.
  # Copy the plugins here so that their dependencies get pulled in.  This is needed
  # since Qt's cocoa platform plugin depends on the QtPrintSupport framework that is
  # otherwise not needed.
  if QtPluginsDir:
    print "------------------------------------------------------------"
    print "Copying Qt plugins "
    print "  %s ==> .../Contents/Plugins" % QtPluginsDir
    print commands.getoutput('mkdir "%s/Contents/Plugins"' % App)
    print commands.getoutput('cp -vR "%s/printsupport" "%s/Contents/Plugins/printsupport"' % (QtPluginsDir, App))
    print commands.getoutput('cp -vR "%s/platforms" "%s/Contents/Plugins/platforms"' % (QtPluginsDir, App))


  # Find libraries inside the package already.
  libraries = commands.getoutput('find %s -type f | xargs file | grep -i "Mach-O.*shared library" | sed "s/:.*//" | cut -d\\  -f1 | sort' % App)
  libraries = libraries.split()
  print "Found %d libraries within the package." % len(libraries)

  # Find external libraries. Any libraries referred to with @.* relative paths are treated as already in the package.
  # ITS NOT THIS SCRIPT'S JOB TO FIX BROKEN INSTALL RULES.

  external_libraries = commands.getoutput(
    'find %s | xargs file | grep "Mach-O" | sed "s/:.*//" | cut -d\\  -f1 | xargs otool -l | grep " name" | sort | uniq | sed "s/name\ //" | grep -v "@" | sed "s/ (offset.*)//"' % App)

  mLibraries = set()
  for lib in external_libraries.split():
    if not isexcluded(lib):
      print "Processing ", lib
      mLibraries.add(Library.createFromReference(lib, "%s/Contents/MacOS/foo" % App))

  print "Found %d direct external dependencies." % len(mLibraries)

  def recursive_dependency_scan(base, to_scan):
    dependencies = set()
    for lib in to_scan:
      dependencies.update(lib.dependencies("%s/Contents/MacOS" % App))
    dependencies -= base
    # Now we have the list of non-packaged dependencies.
    dependencies_to_package = set()
    for dep in dependencies:
      if not isexcluded(dep.RealPath):
        dependencies_to_package.add(dep)
    if len(dependencies_to_package) > 0:
      new_base = base | dependencies_to_package
      dependencies_to_package |= recursive_dependency_scan(new_base, dependencies_to_package)
      return dependencies_to_package
    return dependencies_to_package

  indirect_mLibraries = recursive_dependency_scan(mLibraries, mLibraries)
  print "Found %d indirect external dependencies." % (len(indirect_mLibraries))
  print ""
  mLibraries.update(indirect_mLibraries)

  print "------------------------------------------------------------"
  install_name_tool_command = []
  for dep in mLibraries:
    old_id = dep.Id
    dep.copyToApp(App)
    new_id = dep.Id
    install_name_tool_command += ["-change", '"%s"' % old_id, '"%s"' % new_id]
    if dep.LinkPath is not None:
      install_name_tool_command += ["-change", '"%s"' % dep.LinkPath, '"%s"' % new_id]
  print ""

  install_name_tool_command = " ".join(install_name_tool_command)

  print "------------------------------------------------------------"
  print "Running 'install_name_tool' to fix paths to copied files."
  print ""
  # Run the command for all libraries and executables.
  # The --separator for file allows helps use locate the file name accurately.
  binaries_to_fix = commands.getoutput('find %s -type f | xargs file --separator ":--:" | grep -i ":--:.*Mach-O" | sed "s/:.*//" | cut -d\\  -f1 | sort | uniq ' % App).split()


  result = ""
  for dep in binaries_to_fix:
    commands.getoutput('chmod u+w "%s"' % dep)
  #  print "Fixing '%s'" % dep
    commands.getoutput('install_name_tool %s "%s"' % (install_name_tool_command, dep))
    commands.getoutput('chmod a-w "%s"' % dep)
