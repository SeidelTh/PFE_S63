/*
 * mcp3008-machine.c - Machine driver ASoC pour l'entrée audio via MCP3008
 *
 * Ce driver crée une carte audio qui relie le CPU DAI (l'interface audio de la plateforme)
 * au codec virtuel MCP3008. Il définit un DAI link en utilisant la nouvelle API ASoC.
 */

#include <linux/module.h>
#include <linux/platform_device.h>
#include <sound/soc.h>

/* Définition de la liaison DAI en utilisant les tableaux de composants */
static struct snd_soc_dai_link mcp3008_dai_link = {
    .name = "MCP3008 Audio",
    .stream_name = "MCP3008 Capture",
    .cpus = (struct snd_soc_dai_link_component[]){
        {
            .name = "spi0.0",
            .dai_name = "spi-bcm2835",   /* Remplacer par le nom réel du CPU DAI */
        }
    },
    .num_cpus = 1,
    .codecs = (struct snd_soc_dai_link_component[]){
        {
            .name = "mcp3008-codec",     /* Nom du codec tel qu'enregistré par le driver SPI */
            .dai_name = "mcp3008-dai",   /* Doit correspondre au DAI défini dans le codec */
        }
    },
    .num_codecs = 1,
//    .platforms = (struct snd_soc_dai_link_component[]){
//        {
//            .name = "soc-audio",         /* Nom générique ou spécifique à la plateforme */
//        }
//    },
//    .num_platforms = 1,
    .dai_fmt = SND_SOC_DAIFMT_I2S | SND_SOC_DAIFMT_NB_NF |
               SND_SOC_DAIFMT_CBS_CFS,
    .ignore_pmdown_time = 1,
};

static struct snd_soc_card mcp3008_card = {
    .name     = "mcp3008-card",
    .owner    = THIS_MODULE,
    .dai_link = &mcp3008_dai_link,
    .num_links = 1,
};

static int mcp3008_machine_probe(struct platform_device *pdev)
{
    int ret;
    dev_info(&pdev->dev, "machine probing"); // this is never printed in dmesg
    mcp3008_card.dev = &pdev->dev;
        // Store private data (important for ASoC infrastructure)
    snd_soc_card_set_drvdata(&mcp3008_card, pdev);
    ret = snd_soc_register_card(&mcp3008_card);
    if (ret)
        dev_err(&pdev->dev, "Erreur lors de l'enregistrement de la carte audio: %d\n", ret);
    else
        dev_info(&pdev->dev, "Carte audio MCP3008 enregistrée avec succès\n");
    return ret;
}

static int mcp3008_machine_remove(struct platform_device *pdev)
{
    snd_soc_unregister_card(&mcp3008_card);
    return 0;
}

static const struct of_device_id mcp3008_machine_of_match[] = {
    { .compatible = "custom,mcp3008-machine", },
    { },
};
MODULE_DEVICE_TABLE(of, mcp3008_machine_of_match);

static struct platform_driver mcp3008_machine_driver = {
    .driver = {
        .name = "mcp3008-machine",
        .of_match_table = mcp3008_machine_of_match,
        .owner = THIS_MODULE,
    },
    .probe = mcp3008_machine_probe,
    .remove = mcp3008_machine_remove,
};

module_platform_driver(mcp3008_machine_driver);

MODULE_DESCRIPTION("Machine driver ASoC pour MCP3008");
MODULE_AUTHOR("SEIDEL");
MODULE_LICENSE("GPL");
