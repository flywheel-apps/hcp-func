#!/bin/bash

set -e

if [ $# -lt 1 ] || [[ $1 =~ ^--?(h|help)$ ]];  then
	echo -e `basename $0`" <inputvol> <slicedim> <nsteps> <outputimage> [FSL slicer args]
  inputvol = nifti volume
  slicedim = x,y or z
  nsteps = skip slices
  outputimage = png filename
	"
	exit 0
fi

inputvol=$1
inputvol2=
if [[ ! -z "$2" ]] && [[ `imtest "$2"` = 1 ]]; then
  inputvol2=$2
  shift
fi

slicedim=$2
nsteps=$3
outputimage=$4
shift 4

options=$@

#check for image scale "-s <scale>" options (need to scale output width computation)
imgscale=
while [ $# -gt 0 ]; do
  case $1 in
    -s )
      imgscale=$2
      ;;
  esac
  shift 
done
imgscale=$( echo $imgscale 1 | awk '{print $1}' )

#do dimension swapping based on $slicedim
newdims=
case $slicedim in
  1 | x )
    newdims="y z x"
    ;;
  2 | y )
    newdims="-x z y"
    ;;
  3 | z )
    newdims=
    ;;
  *)
    echo "Invalid slice dimension: $slicedim"
    exit 1
    ;;
esac

tmpd=$(mktemp -d)

if [[ -z "$newdims" ]]; then
  newvol=$inputvol
  newvol2=$inputvol2
else
  newvol=$tmpd/swapvol
  fslswapdim $inputvol $newdims $newvol
  
  newvol2=
  if [[ ! -z "$inputvol2" ]]; then
    newvol2=$tmpd/swapvol2
    fslswapdim $inputvol2 $newdims $newvol2
  fi
fi

dim1=$(fslval $newvol dim1)
dim2=$(fslval $newvol dim2)
dim3=$(fslval $newvol dim3)

nslices=$dim3
slicewidth=$dim1

#to make square mosaic, compute imgwidth=ncols*slicewidth
imgwidth=$(python -c "import math
nslices=$nslices
nsteps=$nsteps
slicewidth=$slicewidth
imgscale=$imgscale
nimages=math.ceil(nslices/nsteps)
nmos1=math.ceil(math.sqrt(nimages))
nmos2=math.ceil(nimages/nmos1)
imgwidth=math.ceil(imgscale*slicewidth)*nmos1
print int(imgwidth)")

#set -x
slicer $newvol $newvol2 $options -S $nsteps $imgwidth $outputimage

rm -rf $tmpd