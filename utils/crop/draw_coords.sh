CUR_DIR=`realpath $0`
CUR_DIR=`dirname ${CUR_DIR}`
OUTPUT_DIR=${1}

for f in ${OUTPUT_DIR}/crop_*png
do 
    name=`basename $f .png`
    coord_file=${OUTPUT_DIR}/${name}.txt
    output_file=${OUTPUT_DIR}/${name}_bbox.png
    python ${CUR_DIR}/draw_coords.py -i $f -c ${coord_file} -o ${output_file}
done
