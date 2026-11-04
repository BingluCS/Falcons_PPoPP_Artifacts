#!/usr/bin/env bash

#set -e

TARGET="$1"


if [ ! -z "$2" ]; then
    CPU_ARCH="$2"
fi

get_cpu_flag() {
    local lib="$1"
    local arch="$2"

    case "$lib" in
        Falcons|falcons)
            case "$arch" in
                AVX2|avx2)
                    echo "-DENABLE_AVX2=ON"
                    ;;
                SVE2|sve2)
                    echo "-DENABLE_SVE2=ON"
                    ;;
                *)
                    echo "-DENABLE_AVX2=OFF -DENABLE_SVE2=OFF"
                    ;;
            esac
            ;;
        SPERR)
            case "$arch" in
                AVX2|avx2)
                    echo "-DENABLE_AVX2=ON"
                    ;;
                *)
                    echo "-DENABLE_AVX2=OFF"
                    ;;
            esac
            ;;
        *)
            echo ""
            ;;
    esac
}

CPU_ARCH = -DENABLE_AVX2=ON

build_PFPL() {
    echo "installing PFPL..."
    cd PFPL
    make
    cd ..
}

build_zfp() {
    echo "installing zfp..."
    cd zfp
    make ZFP_WITH_OPENMP=ON
    cd ..
}

build_SZ3() {
    echo "installing SZ3..."
    cd SZ3
    mkdir build 
    cd build
    cmake .. -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=$(pwd)
    make install -j
    cd ../..
}

build_Falcons() {
    echo "installing Falcons..."
    cd Falcons
    mkdir build
    cd build
    # CPU_FLAG=$(get_cpu_flag "Falcons" "$CPU_ARCH")
    cmake .. -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=$(pwd) $CPU_FLAG #-DENABLE_AVX2=ON
    make install -j
    cd ../..
}

build_SPERR() {
    echo "installing SPERR..."
    cd SPERR
    mkdir build
    cd build
    # CPU_FLAG=$(get_cpu_flag "SPERR" "$CPU_ARCH")
    cmake ..  -DUSE_OMP=ON  $CPU_FLAG #-DENABLE_AVX2=ON
    make -j
    cd ../..
}

build_mgard() {
    echo "installing MGARD..."
    bash build-mgard.sh
}

# build_tthresh() {
#     echo "installing tthresh..."
#     cd tthresh
#     mkdir build
#     cd build
#      cmake -DCMAKE_BUILD_TYPE=Release ..
#     cd ../..
# }
case "$TARGET" in
    PFPL|pfpl)
        build_PFPL
        ;;
    zfp|ZFP)
        build_zfp
        ;;
    SZ3)
	build_SZ3
	;;
    Falcons|falcons)
	build_Falcons
	;;
    SPERR)
	build_SPERR
	;;
    MGARD|mgard)
	build_mgard
	;;
    all)
        build_PFPL
        build_zfp
        build_SZ3
        build_Falcons
        build_SPERR
        # build_mgard
        ;;
    *)
        echo "Usage: $0 {PFPL|pfpl|zfp|ZFP|SZ3|Falcons|falcons|SPERR|all}"
#        exit 1
        ;;
esac