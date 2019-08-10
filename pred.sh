## Arguments
IMAGE_FILE=${1}
CHECKPOINT_DIR=${2:-checkpoint_mlt}
DETAIL=${3:-false}

if [[ ${IMAGE_FILE} != *.png ]]
then
    echo "Image is not png. Failed"
    exit 1
fi

## Names
IMAGE_FILENAME=`basename ${IMAGE_FILE} .png`

## Current directory
CUR_DIR=`realpath ${0}`
CUR_DIR=`dirname ${CUR_DIR}`

## Directory paths
OUTPUT_DIR=${CUR_DIR}/output/${IMAGE_FILENAME}

# Create output directory and copy image there
SECONDS=0
echo Processing in ${OUTPUT_DIR}
mkdir -p ${OUTPUT_DIR}
cp -n ${IMAGE_FILE} ${OUTPUT_DIR}/

## Tile image
echo Tiling..
sleep 0.5

TILE_BASE_RATIO=0.4
width=`identify -format "%w" ${IMAGE_FILE}`
height=`identify -format "%h" ${IMAGE_FILE}`
aspect_ratio=`bc -l <<< "${width}/${height}"`
TILE_RATIO=`bc <<< "scale=2; ${TILE_BASE_RATIO}*${aspect_ratio}"`
echo Tile ratio is ${TILE_RATIO}

tile_coord_file=${OUTPUT_DIR}/${IMAGE_FILENAME}_tile_coordinates.txt
tile_directory=${OUTPUT_DIR}/tiles
if [ -f ${tile_coord_file} ]
then
    echo ${tile_coord_file} exists. PASSED.
else
    if ${DETAIL}
    then
        python ${CUR_DIR}/utils/tile_image.py -i ${IMAGE_FILE} -o ${tile_coord_file} -t ${TILE_RATIO} -w
    else
        python ${CUR_DIR}/utils/tile_image.py -i ${IMAGE_FILE} -o ${tile_coord_file} -t ${TILE_RATIO}
    fi
fi

## Detect lines
echo
echo Detecting lines..
sleep 0.5
python ${CUR_DIR}/main/pred.py --images_dir ${tile_directory} --output_dir ${tile_directory} --checkpoint_dir ${CHECKPOINT_DIR} --gpu 0

## Fix (get to page-relative coordinates) lines
echo
echo Fixing lines..
sleep 0.5
line_coord_file=${OUTPUT_DIR}/${IMAGE_FILENAME}_line_coordinates.txt
if [ -f ${line_coord_file} ]
then
    echo ${line_coord_file} exists. PASSED.
else
    python ${CUR_DIR}/utils/fix_bbox_coords.py -d ${tile_directory} -o ${line_coord_file} -t ${tile_coord_file}
    if ${DETAIL}
    then
        unmerged_bbox_image_file=${OUTPUT_DIR}/${IMAGE_FILENAME}_unmerged_bbox.png
        python ${CUR_DIR}/utils/draw_coords.py -i ${IMAGE_FILE} -o ${unmerged_bbox_image_file} -c ${line_coord_file}
    fi
fi

## Merge overlapping lines
echo
echo Merging lines..
sleep 0.5
output_coord_file=${OUTPUT_DIR}/${IMAGE_FILENAME}_coordinates.txt
if [ -f ${output_coord_file} ]
then
    echo ${output_coord_file} exists. PASSED.
else
    python ${CUR_DIR}/utils/merge_bbox_coords.py -o ${output_coord_file} -c ${line_coord_file}
    if ${DETAIL}
    then
        output_bbox_image_file=${OUTPUT_DIR}/${IMAGE_FILENAME}_bbox.png
        python ${CUR_DIR}/utils/draw_coords.py -i ${IMAGE_FILE} -o ${output_bbox_image_file} -c ${output_coord_file}
    fi
fi

## Drawing crop bboxes
echo
echo Drawing tile lines..
sleep 0.5
if ${DETAIL}
then
    ${CUR_DIR}/utils/draw_coords.sh ${OUTPUT_DIR}/tiles
fi

echo
duration=${SECONDS}
echo "${duration} seconds elapsed."
