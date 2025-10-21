cmake_minimum_required(VERSION 3.16.3...3.19.7 FATAL_ERROR)

project(TMJExtension)

#-----------------------------------------------------------------------------
# Extension meta-information
set(EXTENSION_HOMEPAGE "https://github.com/YourUsername/TMJExtension")
set(EXTENSION_CATEGORY "TMJ Analysis")
set(EXTENSION_CONTRIBUTORS "Your Name (Your Organization)")
set(EXTENSION_DESCRIPTION "This is a 3D Slicer extension for TMJ (Temporomandibular Joint) analysis")
set(EXTENSION_ICONURL "https://raw.githubusercontent.com/YourUsername/TMJExtension/main/TMJExtension/Resources/Icons/TMJExtension.png")
set(EXTENSION_SCREENSHOTURLS "https://raw.githubusercontent.com/YourUsername/TMJExtension/main/Screenshots/Screenshot1.png")
set(EXTENSION_DEPENDS "NA") # Specified as a list or "NA" if no dependencies

#-----------------------------------------------------------------------------
# Extension dependencies
find_package(Slicer REQUIRED)
include(${Slicer_USE_FILE})

#-----------------------------------------------------------------------------
# Extension modules
add_subdirectory(TMJExtension)

#-----------------------------------------------------------------------------
include(${Slicer_EXTENSION_GENERATE_CONFIG})
include(${Slicer_EXTENSION_CPACK})
