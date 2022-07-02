import React, {useState, useRef} from 'react'
import Container from 'react-bootstrap/Container';
import Button from 'react-bootstrap/Button';
import Form from 'react-bootstrap/Form';

import ReactCrop, {
    centerCrop,
    makeAspectCrop,
    Crop,
    PixelCrop,
} from 'react-image-crop'
import {canvasPreview} from './canvasPreview.ts'
import {imgPreview} from "./imgPreview";
import {useDebounceEffect} from './useDebounceEffect.ts'

import 'react-image-crop/dist/ReactCrop.css'

let BG_ASPECT = 2480 / 1212
let AV_ASPECT = 1

// This is to demonstate how to make and center a % aspect crop
// which is a bit trickier so we use some helper functions.
function centerAspectCrop(
    mediaWidth: number,
    mediaHeight: number,
    aspect: number,
) {
    return centerCrop(
        makeAspectCrop(
            {
                unit: '%',
                width: 80,
            },
            aspect,
            mediaWidth,
            mediaHeight,
        ),
        mediaWidth,
        mediaHeight,
    )
}

export default function App() {
    const [bgImgSrc, setBgImgSrc] = useState('')
    const [avImgSrc, setAvImgSrc] = useState('')
    const previewCanvasRef1 = useRef<HTMLCanvasElement>(null)
    const previewCanvasRef2 = useRef<HTMLCanvasElement>(null)
    const bgImgRef = useRef<HTMLImageElement>(null)
    const avImgRef = useRef<HTMLImageElement>(null)
    const [bgCrop, setBgCrop] = useState<Crop>()
    const [avCrop, setAvCrop] = useState<Crop>()
    const [completedBgCrop, setCompletedBgCrop] = useState<PixelCrop>()
    const [completedAvCrop, setCompletedAvCrop] = useState<PixelCrop>()
    const [bgAspect, setBgAspect] = useState<number | undefined>(BG_ASPECT)
    const [avAspect, setAvAspect] = useState<number | undefined>(AV_ASPECT)

    function onSelectFileForBg(e: React.ChangeEvent<HTMLInputElement>) {
        if (e.target.files && e.target.files.length > 0) {
            setBgCrop(undefined) // Makes bgCrop preview update between images.
            const reader = new FileReader()
            reader.addEventListener('load', () =>
                setBgImgSrc(reader.result.toString() || ''),
            )
            reader.readAsDataURL(e.target.files[0])
        }
    }

    function onSelectFileForAv(e: React.ChangeEvent<HTMLInputElement>) {
        if (e.target.files && e.target.files.length > 0) {
            setAvCrop(undefined) // Makes bgCrop preview update between images.
            const reader = new FileReader()
            reader.addEventListener('load', () =>
                setAvImgSrc(reader.result.toString() || ''),
            )
            reader.readAsDataURL(e.target.files[0])
        }
    }

    function onImageLoadBg(e: React.SyntheticEvent<HTMLImageElement>) {
        if (bgAspect) {
            const {width, height} = e.currentTarget
            setBgCrop(centerAspectCrop(width, height, bgAspect))
        }
    }

    function onImageLoadAv(e: React.SyntheticEvent<HTMLImageElement>) {
        if (avAspect) {
            const {width, height} = e.currentTarget
            setAvCrop(centerAspectCrop(width, height, avAspect))
        }
    }

    // @ts-ignore
    useDebounceEffect(
        async () => {
            if (
                completedBgCrop?.width &&
                completedBgCrop?.height &&
                bgImgRef.current &&
                previewCanvasRef1.current
            ) {
                // We use canvasPreview as it's much faster than imgPreview.
                canvasPreview(
                    bgImgRef.current,
                    previewCanvasRef1.current,
                    completedBgCrop
                )
            }
        },
        100,
        [completedBgCrop],
    )
    // @ts-ignore
    useDebounceEffect(
        async () => {
            if (
                completedAvCrop?.width &&
                completedAvCrop?.height &&
                avImgRef.current &&
                previewCanvasRef2.current
            ) {
                // We use canvasPreview as it's much faster than imgPreview.
                canvasPreview(
                    avImgRef.current,
                    previewCanvasRef2.current,
                    completedavCrop
                )
            }
        },
        100,
        [completedAvCrop],
    )

    return (
        <Container className="p-3">
            <Form
                action="http://localhost:8000/process"
                method="POST"
                enctype="multipart/form-data"
            >
                <div className="mb-3 width-500">
                    <label htmlFor="formFile" className="form-label fs-3">1. Загрузите фон</label>
                    <input className="form-control" type="file" name="original_background_image" accept="image/*"
                           onChange={onSelectFileForBg}/>
                </div>
                <div className="width-500">
                    {Boolean(bgImgSrc) && (
                        <ReactCrop
                            crop={bgCrop}
                            onChange={(_, percentCrop) => setBgCrop(percentCrop)}
                            onComplete={(c) => setCompletedBgCrop(c)}
                            aspect={bgAspect}
                        >
                            <img
                                ref={bgImgRef}
                                alt="Crop me"
                                src={bgImgSrc}
                                onLoad={onImageLoadBg}
                            />
                        </ReactCrop>
                    )}
                </div>

                <div className="mb-3 width-500">
                    <label htmlFor="formFile" className="form-label fs-3">2. Загрузите картинку персонажа</label>
                    <input className="form-control" type="file" name="original_avatar_image" accept="image/*"
                           onChange={onSelectFileForAv}/>
                </div>
                <div className="width-500">
                    {Boolean(avImgSrc) && (
                        <ReactCrop
                            crop={avCrop}
                            onChange={(_, percentCrop) => setAvCrop(percentCrop)}
                            onComplete={(c) => setCompletedAvCrop(c)}
                            aspect={avAspect}>
                            <img
                                ref={avImgRef}
                                alt="Crop me"
                                src={avImgSrc}
                                onLoad={onImageLoadAv}
                            />
                        </ReactCrop>
                    )}
                </div>

                <Button type="submit">
                    Process
                </Button>
                <input type="hidden" name="background_crop" value={JSON.stringify(completedBgCrop)}/>
                <input type="hidden" name="background_scale" value={bgImgRef.current && (bgImgRef.current.naturalWidth / bgImgRef.current.width)}/>
                <input type="hidden" name="background_aspect" value={BG_ASPECT}/>
                <input type="hidden" name="avatar_crop" value={JSON.stringify(completedAvCrop)}/>
                <input type="hidden" name="avatar_scale" value={avImgRef.current && (avImgRef.current.naturalWidth / avImgRef.current.width)}/>
                <input type="hidden" name="avatar_aspect" value={AV_ASPECT}/>
            </Form>
        </Container>
    )
}
