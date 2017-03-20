set(VTK_SMP_IMPLEMENTATION_TYPE "Sequential")
if (tbb_ENABLED)
  set(VTK_SMP_IMPLEMENTATION_TYPE "TBB")
endif ()

set(paraview_extra_cmake_args)
if (QT_HELP_GENERATOR)
  list(APPEND paraview_extra_cmake_args
    -DQT_HELP_GENERATOR:FILEPATH=${QT_HELP_GENERATOR})
else()
  list(APPEND paraview_extra_cmake_args
    -DPARAVIEW_ENABLE_EMBEDDED_DOCUMENTATION:BOOL=OFF)
endif()
if (QT_XMLPATTERNS_EXECUTABLE)
  list(APPEND paraview_extra_cmake_args
    -DQT_XMLPATTERNS_EXECUTABLE:FILEPATH=${QT_XMLPATTERNS_EXECUTABLE})
endif()

set(_python_version 2)

if(APPLE)
  set(_python_version 3)
endif()

add_external_project(paraview
  DEPENDS qt python ffmpeg
  DEPENDS_OPTIONAL tbb png

  CMAKE_ARGS
    -DBUILD_SHARED_LIBS:BOOL=ON
    -DBUILD_TESTING:BOOL=OFF
    -DVTK_RENDERING_BACKEND:STRING=OpenGL2
    -DVTK_INSTALL_LIBRARY_DIR:STRING=lib/paraview
    -DVTK_INSTALL_ARCHIVE_DIR:STRING=lib/paraview
    -DVTK_INSTALL_DATA_DIR:STRING=share/paraview
    -DVTK_INSTALL_DOC_DIR:STRING=share/doc/paraview
    -DVTK_CUSTOM_LIBRARY_SUFFIX:STRING=
    -DVTK_PYTHON_FULL_THREADSAFE:BOOL=ON
    -DVTK_NO_PYTHON_THREADS:BOOL=OFF
    -DVTK_PYTHON_VERSION:STRING=${_python_version}
    -DPARAVIEW_QT_VERSION:STRING=5
    -DPARAVIEW_BUILD_QT_GUI:BOOL=ON
    -DPARAVIEW_ENABLE_PYTHON:BOOL=ON
    -DPARAVIEW_ENABLE_CATALYST:BOOL=OFF
    -DPARAVIEW_ENABLE_WEB:BOOL=ON
    -DPARAVIEW_USE_QTHELP:BOOL=OFF
    -DPARAVIEW_BUILD_PLUGIN_AdiosReader:BOOL=FALSE
    -DPARAVIEW_BUILD_PLUGIN_AnalyzeNIfTIIO:BOOL=FALSE
    -DPARAVIEW_BUILD_PLUGIN_ArrowGlyph:BOOL=FALSE
    -DPARAVIEW_BUILD_PLUGIN_CatalystScriptGeneratorPlugin:BOOL=FALSE
    -DPARAVIEW_BUILD_PLUGIN_EyeDomeLighting:BOOL=FALSE
    -DPARAVIEW_BUILD_PLUGIN_ForceTime:BOOL=FALSE
    -DPARAVIEW_BUILD_PLUGIN_GMVReader:BOOL=FALSE
    -DPARAVIEW_BUILD_PLUGIN_H5PartReader:BOOL=FALSE
    -DPARAVIEW_BUILD_PLUGIN_LagrangianParticleTracker:BOOL=FALSE
    -DPARAVIEW_BUILD_PLUGIN_MantaView:BOOL=FALSE
    -DPARAVIEW_BUILD_PLUGIN_MobileRemoteControl:BOOL=FALSE
    -DPARAVIEW_BUILD_PLUGIN_Moments:BOOL=FALSE
    -DPARAVIEW_BUILD_PLUGIN_NonOrthogonalSource:BOOL=FALSE
    -DPARAVIEW_BUILD_PLUGIN_PacMan:BOOL=FALSE
    -DPARAVIEW_BUILD_PLUGIN_PointSprite:BOOL=FALSE
    -DPARAVIEW_BUILD_PLUGIN_PrismPlugin:BOOL=FALSE
    -DPARAVIEW_BUILD_PLUGIN_pvblot:BOOL=FALSE
    -DPARAVIEW_BUILD_PLUGIN_PythonQt:BOOL=FALSE
    -DPARAVIEW_BUILD_PLUGIN_QuadView:BOOL=FALSE
    -DPARAVIEW_BUILD_PLUGIN_SLACTools:BOOL=FALSE
    -DPARAVIEW_BUILD_PLUGIN_SciberQuestToolKit:BOOL=FALSE
    -DPARAVIEW_BUILD_PLUGIN_SierraPlotTools:BOOL=FALSE
    -DPARAVIEW_BUILD_PLUGIN_StreamLinesRepresentation:BOOL=FALSE
    -DPARAVIEW_BUILD_PLUGIN_StreamingParticles:BOOL=FALSE
    -DPARAVIEW_BUILD_PLUGIN_SurfaceLIC:BOOL=FALSE
    -DPARAVIEW_BUILD_PLUGIN_UncertaintyRendering:BOOL=FALSE
    -DPARAVIEW_BUILD_PLUGIN_VRPlugin:BOOL=FALSE
    -DPARAVIEW_BUILD_PLUGIN_VaporPlugin:BOOL=FALSE
    -DPARAVIEW_BUILD_PLUGIN_RGBZView:BOOL=OFF
    -DPQWIDGETS_DISABLE_QTWEBKIT:BOOL=ON
    -DPARAVIEW_ENABLE_FFMPEG:BOOL=ON
    -DModule_vtkGUISupportQtWebkit:BOOL=OFF
    -DCMAKE_CXX_STANDARD:STRING=11
    -DCMAKE_CXX_STANDARD_REQUIRED:BOOL=ON
    -DVTK_SMP_IMPLEMENTATION_TYPE:STRING=${VTK_SMP_IMPLEMENTATION_TYPE}

    ${paraview_extra_cmake_args}

    # specify the apple app install prefix. No harm in specifying it for all
    # platforms.
    -DMACOSX_APP_INSTALL_PREFIX:PATH=<INSTALL_DIR>/Applications

  LIST_SEPARATOR +
)
